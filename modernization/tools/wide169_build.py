"""Build the isolated 1280x720 candidate; never mutate the accepted runtime."""
from pathlib import Path
import hashlib, json, struct, shutil, re, io, argparse
import pefile, capstone
from PIL import Image
import hd_hud_build as hd
import display
from qwen_canvas import grimoire_key_template, apply_grimoire_key_template

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / 'game'
LAB = ROOT / 'game-wide169'
BUILD = ROOT / 'modernization/build/wide169'
SOURCE_SHA = hd.SOURCE_SHA

def sha(data): return hashlib.sha256(data).hexdigest()
def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')

def build_engine():
    data = (GAME/'Chaos.exe').read_bytes()
    if sha(data) != SOURCE_SHA: raise RuntimeError('Unknown community engine')
    qol=json.loads((ROOT/'modernization/hd-qol-trial-installed.json').read_text())
    for name,expected in qol['files'].items():
        if sha((ROOT/name).read_bytes())!=expected:raise RuntimeError('Latest QoL input changed: '+name)
    latest=(ROOT/qol['engine']).read_bytes()
    baseline=json.loads((ROOT/'modernization/current-baseline.json').read_text())
    for name in ('Chaos-HD60-Trial.exe','Chaos-HD60-engine.exe'):
        if sha((GAME/name).read_bytes()) != baseline['files'][name]:
            raise RuntimeError('Accepted HD60 identity changed: '+name)
    pe=pefile.PE(data=data); out=bytearray(data); changes=[]
    decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); decoder.detail=True
    def patch(va, old, new, label):
        off=pe.get_offset_from_rva(va-0x400000)
        if data[off:off+len(old)]!=old: raise RuntimeError(f'Wrong bytes at {va:x}')
        out[off:off+len(old)]=new
        changes.append(dict(va=hex(va),before=old.hex(),after=new.hex(),label=label))
    def integer(va,old,new,label):patch(va,struct.pack('<I',old),struct.pack('<I',new),label)
    for va,(old,new) in (hd.PATCHES|hd.RECT_PATCHES).items():
        value={640:1120,480:600,800:1280,600:720}[old]
        integer(va,old,value,'1280x720 primary/battle rectangle')
    sites=hd.HUD_SITES|hd.UI_SURFACE_SITES|hd.GRIMOIRE_SITES|hd.ADDITIONAL_SCREEN_SITES|hd.TEST5_SITES
    for va,(mnemonic,old,delta,label) in sites.items():
        if 'loading bar' in label:
            if 'bottom anchor' in label: new=578 # +120 = 698; 22px bar-to-bottom spacing
            elif 'centring remainder' in label: new=202 # +80 =282, centered 716px active width
            elif old==598:new=718
            elif old==36:new=43
            else:raise RuntimeError(label)
        elif va==0x54FDC0: new=960 # content right 1120, minus native high-res +160
        elif 'Grimoire' in label:
            new=old+({320:480,240:120,160:240}[delta])
        else:
            new=old+({320:480,240:120}[delta])
        ins=next(decoder.disasm(data[pe.get_offset_from_rva(va-0x400000):][:15],va,1))
        field=ins.disp_offset if mnemonic=='lea' else ins.imm_offset
        size=ins.disp_size if mnemonic=='lea' else ins.imm_size
        if ins.mnemonic!=mnemonic or size not in (1,4):raise RuntimeError(hex(va))
        patch(va+field,old.to_bytes(size,'little'),new.to_bytes(size,'little'),label)
    # Character screen has additional full-surface copies outside the generic
    # creator sites. Without these, the native portrait is drawn in the left bar.
    # Resource filename selectors stay at 800x600; only portrait centring uses
    # the full canvas dimensions. Patching selectors would require new folders.
    character_size_sites=(0x4B5B50,0x4B5B76)
    for va in character_size_sites:
        off=pe.get_offset_from_rva(va-0x400000)
        ins=next(decoder.disasm(data[off:off+15],va,1))
        if ins.mnemonic not in ('add','lea') or ins.imm_size!=4:raise RuntimeError('Character site '+hex(va))
        field=off+ins.imm_offset;old=struct.unpack_from('<I',data,field)[0]
        if old not in (640,480):raise RuntimeError('Character dimension '+hex(va))
        patch(va+ins.imm_offset,struct.pack('<I',old),struct.pack('<I',800 if old==640 else 600),'character portrait 480x360 surface')
    face_cave=0x5C42E0
    face_code=bytes.fromhex('8144242ca0000000a1e41e6e00')+b'\xe9'+struct.pack('<i',0x4B5C31-(face_cave+18))
    patch(face_cave,b'\x00'*len(face_code),face_code,'character portrait centered destination')
    patch(0x4B5C2C,bytes.fromhex('a1e41e6e00'),b'\xe9'+struct.pack('<i',face_cave-(0x4B5C2C+5)),'character portrait draw entry')
    # The turn animation recognizes the original high-res branch by width.
    # Each physical page is 640 wide, and its painted half remains 480 wide.
    for width,branch,half,height in hd.GRIMOIRE_DRAW_GROUPS:
        off=pe.get_offset_from_rva(branch-0x400000)
        ins=next(decoder.disasm(data[off:off+15],branch,1))
        if ins.mnemonic!='cmp' or ins.imm_size!=4:raise RuntimeError('Grimoire branch '+hex(branch))
        integer(branch+ins.imm_offset,800,1280,'Grimoire turn high-res branch')
        integer(half+1,400,640,'Grimoire turn page width')
    for va,(old,new,label) in hd.GRIMOIRE_FORMAT_SITES.items():
        integer(va+1,old,new,label)
    for va,(old,new,label) in hd.GRIMOIRE_LOADER_SITES.items():
        patch(va,b'\xe8'+struct.pack('<i',old-va-5),b'\xe8'+struct.pack('<i',new-va-5),label)
    for address,count in hd.TEST5_TABLES:
        for i in range(count*4):
            va=address+i*4;off=pe.get_offset_from_rva(va-0x400000)
            old=struct.unpack_from('<i',data,off)[0]
            if not 0<=old<=800:raise RuntimeError('Unknown portmanteau table')
            new=(old*6+2)//5+(160 if i%2==0 else 0)
            integer(va,old,new,'centered 960x720 Portmanteau rectangle')
    # Realm map's hit mask remains 800x600. Convert centered visual coordinates
    # (x-160)*800/960, y*600/720 before its original 800-stride mask lookup.
    # The short entry detour uses verified zero padding at the end of .text.
    cave=0x5C42C0
    original=bytes.fromhex('8b44240456')
    entry=b'\xe9'+struct.pack('<i',cave-(0x5505A0+5))
    code=bytes.fromhex('8b4424042da000000056')+b'\xe9'+struct.pack('<i',0x5505A5-(cave+15))
    patch(cave,b'\x00'*len(code),code,'realm mask x origin detour')
    patch(0x5505A0,original,entry,'realm mask x origin entry')
    integer(0x5505C9,640,800,'realm mask x visual denominator 960')
    integer(0x5505D8,480,600,'realm mask y visual denominator 720')
    marker_cave=0x5C4310
    marker_code=bytes.fromhex('6bc10699bf05000000f7ff8bc881c1a00000006bc60699f7ff8bf08b93d7010000')
    marker_code+=b'\xe9'+struct.pack('<i',0x5507C2-(marker_cave+len(marker_code)+5))
    patch(marker_cave,b'\x00'*len(marker_code),marker_code,'realm marker 6/5 centered projection')
    patch(0x5507BC,bytes.fromhex('8b93d7010000'),b'\xe9'+struct.pack('<i',marker_cave-(0x5507BC+5))+b'\x90','realm marker draw projection entry')
    menu_cave=0x5C4350
    menu_code=bytes.fromhex('b818010000b978000000')+b'\xe9'+struct.pack('<i',0x4B26CD-(menu_cave+15))
    patch(menu_cave,b'\x00'*len(menu_code),menu_code,'Esc background centered at 280,120')
    patch(0x4B26BD,bytes.fromhex('b8640000008bc8eb07'),b'\xe9'+struct.pack('<i',menu_cave-(0x4B26BD+5))+b'\x90'*4,'Esc background draw origin')
    # Confirmation dialogs center against the native canvas. Their resource
    # selector still uses 800x600; only the final screen-centering pair grows.
    integer(0x4CF4B3,640,1120,'confirmation screen width')
    integer(0x4CF4DA,480,600,'confirmation screen height')
    patch(0x4E5543,bytes.fromhex('e85c700b00'),bytes.fromhex('b858020000'),'accepted route limit 600')
    from build_hd60_engine import RUNTIME_SITES
    for va,expected in RUNTIME_SITES.items():
        off=pe.get_offset_from_rva(va-0x400000)
        if out[off:off+len(expected)]!=expected:raise RuntimeError('Runtime hook conflict')
    BUILD.mkdir(parents=True,exist_ok=True)
    # Overlay only the audited wide-layout fields onto the latest QoL engine.
    # Preserve every byte outside these explicit changes, including later fixes.
    merged=bytearray(latest)
    for row in changes:
        off=pe.get_offset_from_rva(int(row['va'],16)-0x400000);new=bytes.fromhex(row['after'])
        merged[off:off+len(new)]=new
    target=BUILD/'Chaos-Wide169-engine.exe';target.write_bytes(merged)
    write_json(BUILD/'engine.json',dict(source_sha256=SOURCE_SHA,development_base=qol['entry'],development_engine_sha256=sha(latest),sha256=sha(merged),changes=changes))
    return target

def prepare():
    if LAB.exists():raise RuntimeError('Independent runtime already exists; refusing recopy')
    def ignore(folder,names):
        return [n for n in names if Path(folder,n).is_junction() or (Path(folder)==GAME and (n=='modernization' or (n.lower().startswith('chaos') and n.lower().endswith('.exe'))))]
    shutil.copytree(GAME,LAB,ignore=ignore)
    (LAB/'modernization/logs').mkdir(parents=True)
    (LAB/'ss').mkdir()
    write_json(LAB/'wide169-lab.json',dict(kind='independent-wide169',source=str(GAME)))

def assets():
    if not (LAB/'wide169-lab.json').exists():raise RuntimeError('Missing lab marker')
    state=json.loads((ROOT/'modernization/assets/hd/ui-fit.json').read_text())
    backup=ROOT/'modernization/assets/hd/backups/ui-fit'
    keyed=json.loads((ROOT/'modernization/assets/hd/ui-keyed-bmp.json').read_text())
    prior=json.loads((BUILD/'assets.json').read_text()) if (BUILD/'assets.json').exists() else {'files':[]}
    prior_hashes={row['path']:row['sha256'] for row in prior['files']}
    # Remove only the copied generated derivatives, with identity verification.
    for row in keyed['files']:
        path=LAB/row['path']
        if path.exists():
            if sha(path.read_bytes()) not in (row['sha256'],prior_hashes.get(row['path'])):raise RuntimeError('Unexpected derivative')
            path.unlink()
    records=[]
    for index,row in enumerate(state['files']):
        rel=Path(row['path']); raw=(backup/str(index)).read_bytes()
        if sha(raw)!=row['original_sha256']:raise RuntimeError('Backup changed')
        if rel.suffix.lower()=='.cfg':
            def rect(m):
                v=list(map(int,m.groups()[1:]));w=[round(x*1.2) for x in v]
                # Rect2 stores left,top,right,bottom; zero endpoints mark an origin-only sprite.
                w[0]+=160
                if v[2]!=0:w[2]+=160
                return m[1]+b','.join(str(x).encode() for x in w)
            out=re.sub(rb'(?m)^(\s*Rect2\s*=\s*)(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)',rect,raw)
            def named(m):
                name=m[2].lower(); value=round(int(m[3])*1.2)
                if name.endswith((b'x',b'left',b'right')):value+=160
                return m[1]+str(value).encode()
            out=re.sub(rb'(?m)^(\s*800x600_([A-Za-z0-9_]+)\s*=\s*)(-?\d+)',named,out)
            if b'VAR_LAWCOST' in out and b'[SPRITEBAR_3]' in out:
                out=re.sub(rb'(Rect2=484,)(432|492|552)(,0,0)',lambda m:m[1]+str(int(m[2])+6).encode()+m[3],out)
        else:
            image=Image.open(io.BytesIO(raw)).convert('RGB'); size=image.size
            if size==(800,600):
                result=Image.new('RGB',(1280,720));result.paste(image.resize((960,720),Image.Resampling.LANCZOS),(160,0))
            elif size==(400,600):
                # Each page is 480x720 inside a 640x720 compositor half.
                # P1 sits against the central fold; P2 begins at that fold.
                left=bool(re.search(r'P1_|^GenericL',rel.name,re.I))
                template=grimoire_key_template(image)
                scaled=apply_grimoire_key_template(image.resize((480,720),Image.Resampling.NEAREST),template)
                result=Image.new('RGB',(640,720),(0,0,255))
                result.paste(scaled,(160 if left else 0,0))
                bmp_rel=rel.with_suffix('.PNG');bmp=io.BytesIO();result.save(bmp,'PNG',compress_level=9,optimize=True)
                (LAB/bmp_rel).write_bytes(bmp.getvalue())
                records.append(dict(path=bmp_rel.as_posix(),source_sha256=sha(raw),sha256=sha(bmp.getvalue()),provenance='original-keyed-page'))
            elif size==(600,400):result=image.resize((720,480),Image.Resampling.LANCZOS)
            elif size==(600,36):result=image.resize((720,43),Image.Resampling.LANCZOS)
            else:raise RuntimeError(f'Unknown source dimensions {rel} {size}')
            buf=io.BytesIO(); lossless=rel.suffix.lower() in ('.bmp','.png'); result.save(buf,'PNG' if lossless else 'JPEG',**({'compress_level':9,'optimize':True} if lossless else {'quality':100,'subsampling':0}));out=buf.getvalue()
            if lossless:rel=rel.with_suffix('.PNG')
        (LAB/rel).write_bytes(out)
        records.append(dict(path=rel.as_posix(),source_sha256=sha(raw),sha256=sha(out)))
    for source in sorted((GAME/'Interface/CharacterScreen/800x600').glob('WizardFace*.JPG')):
        raw=source.read_bytes();image=Image.open(io.BytesIO(raw)).convert('RGB')
        if image.size!=(400,300):raise RuntimeError('Unknown original portrait')
        out=io.BytesIO();image.resize((480,360),Image.Resampling.NEAREST).save(out,'JPEG',quality=100,subsampling=0)
        rel=source.relative_to(GAME);(LAB/rel).write_bytes(out.getvalue())
        records.append(dict(path=rel.as_posix(),source_sha256=sha(raw),sha256=sha(out.getvalue()),provenance='original-portrait-resize'))
    # Fixed tutorial scrolls use their own unscaled coordinates. Keep their
    # existing art size and center it within the 960x720 content region.
    speech_source=GAME/'CFG/speechbox.cfg';raw=speech_source.read_bytes()
    def speech_box(m):
        x,y=map(int,m.groups()[1:]);return m[1]+str(x+240).encode()+b','+str(y+60).encode()
    speech=re.sub(rb'(?m)^(\s*BoxPos\s*=\s*)(\d+)\s*,\s*(\d+)',speech_box,raw)
    (LAB/'CFG/speechbox.cfg').write_bytes(speech)
    records.append(dict(path='CFG/speechbox.cfg',source_sha256=sha(raw),sha256=sha(speech),provenance='centered-original-dialog'))
    prefs=LAB/'CFG/prefs.cfg'
    data=prefs.read_bytes();data=re.sub(rb'(?m)^MaxFramesPerSec=.*$',b'MaxFramesPerSec=30',data);prefs.write_bytes(data)
    ini=LAB/'ddraw.ini'
    ini.write_text(display.update_ddraw(ini.read_text(encoding='cp1252'),dict(width='2560',height='1440',windowed='true',fullscreen='false',maintas='true',boxing='false',savesettings='0',screenshotdir='.\\ss\\')),encoding='cp1252')
    write_json(BUILD/'assets.json',dict(canvas=[1280,720],content=[160,0,1120,720],files=records))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','engine','assets']);a=parser.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='assets':assets()
    else:print(build_engine())
