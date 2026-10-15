"""Stage hash-gated native Region Entry and Grimoire in isolated v3 only."""
from pathlib import Path
import hashlib
import json
import re
import struct
import capstone
import pefile
from PIL import Image
from hd_hud_build import GRIMOIRE_SITES
from wide169_build import ROOT

BASE = ROOT / 'modernization/playtests/mixed-ui-v3'
LAB = BASE / 'game-wide169'
SOURCE = '531ca844330ed03c4314e762a4f23f4b72db9ca30ec88608023103099ab80ac0'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def stage():
    from compare_hd_baseline import baseline_identity
    baseline_identity()
    backup = BASE / 'before-native-pages'
    if backup.exists():
        raise RuntimeError('Existing stage evidence must be retained')
    engine = LAB / 'Chaos-Wide169-engine.exe'
    raw = engine.read_bytes()
    if sha(raw) != SOURCE:
        raise RuntimeError('Unknown candidate engine')
    pe = pefile.PE(data=raw)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    decoder.detail = True
    patched = bytearray(raw)
    patches = []
    sites = dict(GRIMOIRE_SITES)
    sites.update({0x4B2C77: ('add',640,320,'Region Entry backing width'),
                  0x4B2C88: ('add',480,240,'Region Entry backing height')})
    for va, (mnemonic, original, _, label) in sites.items():
        old, new = {'add': {640:(1120,2400),480:(600,1320)},
                    'cmp': {800:(1280,2560)},'mov': {400:(640,1280)}}[mnemonic][original]
        offset = pe.get_offset_from_rva(va-0x400000)
        ins = next(decoder.disasm(raw[offset:offset+15],va,1))
        field = offset + ins.imm_offset
        if ins.mnemonic != mnemonic or ins.imm_size != 4 or struct.unpack_from('<I',raw,field)[0] != old:
            raise RuntimeError(f'Unknown native-page field {va:#x}')
        struct.pack_into('<I',patched,field,new)
        patches.append(dict(va=hex(va),old=old,new=new,label=label))
    backup.mkdir()
    changes = []
    def write(rel, data, provenance):
        path = LAB / rel
        before = path.read_bytes() if path.exists() else None
        saved = backup / rel
        if before is not None:
            saved.parent.mkdir(parents=True,exist_ok=True)
            saved.write_bytes(before)
        path.write_bytes(data)
        changes.append(dict(path=Path(rel).as_posix(),before_sha256=sha(before) if before else None,
                            sha256=sha(data),provenance=provenance))
    write('Chaos-Wide169-engine.exe',bytes(patched),'verified v2 geometry fields')
    for rel in ['Interface/RegionEntry/screen (Region Entry).cfg','Interface/Grimoire/Grimoire.cfg']:
        cfg = (LAB/rel).read_bytes()
        if 'RegionEntry' in rel:
            cfg = re.sub(rb'(?m)^(\s*Rect2\s*=\s*)(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)',
                         lambda m:m[1]+b','.join(str(2*int(m[i])).encode() for i in range(2,6)),cfg)
        else:
            cfg = re.sub(rb'(?m)^(\s*800x600_[A-Za-z0-9_]+\s*=\s*)(-?\d+)',
                         lambda m:m[1]+str(2*int(m[2])).encode(),cfg)
        write(rel,cfg,'double verified wide169 coordinates')
    queue=json.loads((ROOT/'modernization/assets/hd/hd-queue.json').read_text(encoding='utf-8'))
    pack=ROOT/'modernization/assets/hd/pack'
    for row in queue['records']:
        if not (row['source'].startswith('Interface/RegionEntry/800x600/') or
                row['source']=='Interface/Grimoire/800x600/Backdrop.JPG'):
            continue
        png=pack/row['output']
        meta=json.loads(png.with_suffix('.png.json').read_text(encoding='utf-8'))
        if row['status']!='done' or sha(png.read_bytes())!=row['output_sha256'] or meta['source_sha256']!=row['source_sha256']:
            raise RuntimeError('Unverified Qwen raster '+row['source'])
        with Image.open(png) as opened:
            if opened.size!=(1920,1440):raise RuntimeError('Wrong native UI size')
            canvas=Image.new('RGB',(2560,1440));canvas.paste(opened.convert('RGB'),(320,0))
        import io
        buf=io.BytesIO();canvas.save(buf,'JPEG',quality=100,subsampling=0)
        write(row['source'],buf.getvalue(),'Qwen native 1920x1440 centered 1:1; '+row['output_sha256'])
    keyed=ROOT/'modernization/assets/hd/keyed-pages'
    manifest=json.loads((keyed/'manifest.json').read_text(encoding='utf-8'))
    for row in manifest['records']:
        png=keyed/row['output']; producer=pack/Path(row['source']).with_suffix('.png')
        if sha(png.read_bytes())!=row['output_sha256'] or sha(producer.read_bytes())!=row['qwen_png_sha256']:
            raise RuntimeError('Unverified keyed Qwen page')
        with Image.open(png) as opened:
            if opened.size!=(960,1440):raise RuntimeError('Wrong native Grimoire page size')
            canvas=Image.new('RGB',(1280,1440),(0,0,255))
            left=bool(re.search(r'P1_|^GenericL',Path(row['source']).name,re.I))
            canvas.paste(opened.convert('RGB'),(320 if left else 0,0))
        buf=io.BytesIO();canvas.save(buf,'BMP')
        write(Path(row['source']).with_suffix('.BMP'),buf.getvalue(),'Qwen dual-key page 1:1; '+row['output_sha256'])
    report=dict(source_engine_sha256=SOURCE,engine_sha256=sha(bytes(patched)),patches=patches,files=changes,
                status='staged-not-accepted',rollback='Restore files from before-native-pages; delete only newly staged paths listed with null before_sha256')
    (BASE/'native-pages-stage.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(engine_sha256=report['engine_sha256'],files=len(changes),patches=len(patches))))

if __name__=='__main__':stage()
