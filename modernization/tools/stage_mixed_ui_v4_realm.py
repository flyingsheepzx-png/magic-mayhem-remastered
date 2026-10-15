"""Stage native realm map and its Portmanteau entrance in isolated v4 only.

Preserves the 800x600 semantic realm mask and projects the new 1920x1440
visual canvas back to it. Runtime QoL hook updates are built separately.
"""
from pathlib import Path
import hashlib
import io
import json
import shutil
import struct
import capstone
import pefile
from PIL import Image
from wide169_build import ROOT
from compare_hd_baseline import baseline_identity

BASE=ROOT/'modernization/playtests/mixed-ui-v4'
LAB=BASE/'game-wide169'
SOURCE='7327c93dc75a0cf61b377b37a244fc9318cf702da1b06a0ff3484d83578ab20a'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def stage():
    baseline_identity()
    backup=BASE/'before-native-realm'
    if backup.exists():raise RuntimeError('Previous realm stage must be preserved')
    path=LAB/'Chaos-Wide169-engine.exe';raw=path.read_bytes()
    if sha(raw)!=SOURCE:raise RuntimeError('Unknown v4 engine')
    pe=pefile.PE(data=raw);cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);cs.detail=True
    patched=bytearray(raw);changes=[]
    def at(va):return pe.get_offset_from_rva(va-0x400000)
    def instruction(va,mnemonic,old,new,label):
        offset=at(va);ins=next(cs.disasm(raw[offset:offset+15],va,1))
        if ins.mnemonic!=mnemonic or ins.imm_size not in (1,4):raise RuntimeError(f'Unknown instruction {va:#x}')
        field=offset+ins.imm_offset;size=ins.imm_size
        if int.from_bytes(raw[field:field+size],'little')!=old:raise RuntimeError(f'Unknown field {va:#x}')
        patched[field:field+size]=new.to_bytes(size,'little')
        changes.append(dict(va=hex(va),old=old,new=new,label=label))
    for va,old,new,label in [
      (0x54f6f9,1120,2400,'realm backing width'),(0x54f70d,600,1320,'realm backing height'),
      (0x5502ad,1120,2400,'realm refresh width'),(0x5502c8,600,1320,'realm refresh height'),
      (0x54fdc0,960,2080,'realm toolbar right anchor')]:
        instruction(va,'add',old,new,label)
    for va,old,new,label in [(0x5505c9,800,1760,'realm mask visual width 1920'),
                              (0x5505d8,600,1320,'realm mask visual height 1440')]:
        off=at(va)
        if struct.unpack_from('<I',raw,off)[0]!=old:raise RuntimeError(f'Unknown mask denominator {va:#x}')
        struct.pack_into('<I',patched,off,new)
        changes.append(dict(va=hex(va),old=old,new=new,label=label))
    for va,old,new,label in [(0x5c42c4,160,320,'mask visual X origin'),
                              (0x5c4310,6,12,'marker visual X scale numerator'),
                              (0x5c431d,160,320,'marker visual X origin'),
                              (0x5c4323,6,12,'marker visual Y scale numerator')]:
        mnemonic={0x5c42c4:'sub',0x5c4310:'imul',0x5c431d:'add',0x5c4323:'imul'}[va]
        instruction(va,mnemonic,old,new,label)
    # v3 already has the full-size Portmanteau and doubled table; retain it.
    for va,expected in [(0x5778ec,2400),(0x577906,1320),(0x577943,2399),(0x57795c,1319)]:
        if struct.unpack_from('<I',raw,at(va))[0]!=expected:
            raise RuntimeError('Portmanteau baseline geometry changed')
    with Image.open(LAB/'Interface/SpellBox/800x600/Portmanteau.bmp') as port:
        if port.size!=(2560,1440):raise RuntimeError('Portmanteau backing changed')
    queue=json.loads((ROOT/'modernization/assets/hd/hd-queue.json').read_text(encoding='utf-8'))
    selected={'Interface/RealmViewer/800x600/Celtic_Map.bmp',
              'Interface/RealmViewer/800x600/Greek_Map.bmp',
              'Interface/RealmViewer/800x600/Medieval_Map.bmp'}
    records={r['source']:r for r in queue['records'] if r['source'] in selected}
    if set(records)!=selected:raise RuntimeError('Missing Qwen map or Portmanteau record')
    generated=[]
    for rel,row in records.items():
        png=ROOT/'modernization/assets/hd/pack'/row['output']
        meta=json.loads(png.with_suffix('.png.json').read_text(encoding='utf-8'))
        if row['status']!='done' or sha(png.read_bytes())!=row['output_sha256'] or meta['source_sha256']!=row['source_sha256']:
            raise RuntimeError('Unverified Qwen raster '+rel)
        with Image.open(png) as opened:
            if opened.size!=(1920,1440):raise RuntimeError('Wrong Qwen native size')
            canvas=Image.new('RGB',(2560,1440));canvas.paste(opened.convert('RGB'),(320,0))
        buf=io.BytesIO();canvas.save(buf,'BMP');generated.append((rel,buf.getvalue(),row['output_sha256']))
    backup.mkdir();shutil.copy2(path,backup/path.name);path.write_bytes(patched)
    files=[]
    for rel,data,source_sha in generated:
        dest=LAB/rel;old=dest.read_bytes();saved=backup/rel;saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(old);dest.write_bytes(data)
        files.append(dict(path=rel,before_sha256=sha(old),sha256=sha(data),qwen_output_sha256=source_sha))
    report=dict(status='staged-not-accepted',source_engine_sha256=SOURCE,
                engine_sha256=sha(patched),patches=changes,files=files,
                hitmask='original 800x600 mask preserved; visual coordinates subtract 320 and divide by 1920/1440')
    (BASE/'native-realm-stage.json').write_text(json.dumps(report,indent=2)+'\n')
    manifest=json.loads((BASE/'manifest.json').read_text());manifest['files']['game-wide169/Chaos-Wide169-engine.exe']=sha(patched)
    for row in files:manifest['files']['game-wide169/'+row['path']]=row['sha256']
    manifest['status']='v4-development-not-playtest'
    (BASE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(engine_sha256=sha(patched),asset_count=len(files),patches=len(changes))))

if __name__=='__main__':stage()
