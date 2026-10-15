"""Encode verified Qwen Grimoire frames as RGB565 SPR v4 in isolated v3.

Preserve source frame indices, names and exact nearest 2x coverage.
Qwen sheet gutters are cropped using the original alignment origin. All output
frames are independently decoded and checked before any runtime file changes.
"""
from pathlib import Path
import hashlib
import json
import struct
from PIL import Image,ImageChops
from spr_assets import read_spr,decode
from wide169_build import ROOT

BASE=ROOT/'modernization/playtests/mixed-ui-v3'
LAB=BASE/'game-wide169'
PACK=ROOT/'modernization/assets/hd/pack'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def encode(frame,image):
    width,height=image.size
    rows=bytearray(height*8);run_data=bytearray();pixel_data=bytearray();px=image.load()
    for y in range(height):
        runs=bytearray();pixels=bytearray();x=0;paint=False
        while x<width:
            length=0
            while x+length<width and bool(px[x+length,y][3])==paint:length+=1
            remaining=length
            while remaining>255:
                runs.extend((255,0));remaining-=255
            runs.append(remaining)
            if paint:
                for j in range(length):
                    r,g,b,_=px[x+j,y]
                    pixels.extend(struct.pack('<H',(r*31//255)<<11|(g*63//255)<<5|b*31//255))
            x+=length;paint=not paint
        run_offset=40+height*8+len(run_data);run_data.extend(runs)
        pixel_offset=len(pixel_data);pixel_data.extend(pixels)
        struct.pack_into('<II',rows,y*8,run_offset,pixel_offset)
    for y in range(height):
        offset=struct.unpack_from('<I',rows,y*8+4)[0]
        struct.pack_into('<I',rows,y*8+4,40+height*8+len(run_data)+offset)
    payload=run_data+pixel_data
    header=bytearray(frame['data'][:40])
    struct.pack_into('<3I2i',header,0,40+len(rows)+len(payload),width,height,
                     frame['offset'][0]*2,frame['offset'][1]*2)
    # Native loader/blitter uses -1 for RGB frames. +32/+36 are optional
    # mask offsets, not flags; old-size masks cannot refer into the new payload.
    struct.pack_into('<III',header,28,0xffffffff,0,0)
    return bytes(header+rows+payload)

def stage():
    from compare_hd_baseline import baseline_identity
    baseline_identity()
    backup=BASE/'before-grimoire-sprites-r2'
    if backup.exists():raise RuntimeError('Preserve prior sprite-stage evidence')
    if sha((LAB/'Chaos-Wide169-engine.exe').read_bytes())!='c19b01f77a8ae548e2acd027c3e782274380cde0cc4a50de4066167b9795d7ff':
        raise RuntimeError('Unknown v3 engine')
    sources=['Interface/Grimoire/800x600/icons.spr','Interface/Grimoire/Generic/Icons.spr',
             'Interface/Grimoire/Generic/PageTurns.spr']
    staged=[]
    temp=BASE/'sprite-derivatives';temp.mkdir(exist_ok=True)
    for rel in sources:
        path=LAB/rel;raw=path.read_bytes();palettes,frames=read_spr(path)
        meta=json.loads((PACK/rel/'sprite.json').read_text())
        if not meta['complete'] or meta['scale']!=2 or sha(raw)!=meta['source_sha256']:
            raise RuntimeError('Unknown/incomplete Qwen source '+rel)
        usable=[f for f in frames if f['width'] and f['height']]
        origin=[min(f['offset'][i] for f in usable) for i in range(2)]
        records={r['index']:r for r in meta['frames']}
        encoded=[];expected=[]
        for frame in frames:
            if not frame['width']:
                image=Image.new('RGBA',(0,0));encoded.append(encode(frame,image));expected.append(image);continue
            row=records[frame['index']];png=PACK/rel/row['file']
            if sha(png.read_bytes())!=row['sha256'] or row['source_size']!=[frame['width'],frame['height']] or row['offset']!=frame['offset'] or row['flags']!=list(frame['flags']):
                raise RuntimeError('Qwen frame identity mismatch')
            with Image.open(png) as opened:
                if list(opened.size)!=meta['target_frame_size']:raise RuntimeError('Wrong Qwen sheet geometry')
                x,y=[2*(frame['offset'][i]-origin[i]) for i in range(2)]
                image=opened.convert('RGBA').crop((x,y,x+frame['width']*2,y+frame['height']*2))
            mask=decode(palettes,frame).getchannel('A').resize(image.size,Image.Resampling.NEAREST)
            image.putalpha(mask);expected.append(image);encoded.append(encode(frame,image))
        output=bytearray(raw[:24]);offset=0
        struct.pack_into('<II',output,16,0,0)  # RGB565 removes palette blocks.
        for frame in encoded:output.extend(struct.pack('<I',offset));offset+=len(frame)
        for frame in encoded:output.extend(frame)
        struct.pack_into('<I',output,4,len(output))
        target=temp/Path(rel).name
        # The two Icons files share a name; retain their separate directory paths.
        target=temp/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(output)
        new_pal,new_frames=read_spr(target)
        if new_pal or len(new_frames)!=len(frames):raise RuntimeError('SPR roundtrip frame count')
        maximum_error=0
        for old,new,wanted in zip(frames,new_frames,expected):
            actual=decode(new_pal,new)
            if new['offset']!=[x*2 for x in old['offset']] or new['flags']!=(0xffffffff,0,0) or new['name']!=old['name']:
                raise RuntimeError('SPR metadata roundtrip mismatch')
            if ImageChops.difference(actual.getchannel('A'),wanted.getchannel('A')).getbbox():raise RuntimeError('SPR coverage changed')
            diff=ImageChops.difference(actual.convert('RGB'),wanted.convert('RGB'))
            diff=Image.composite(diff,Image.new('RGB',diff.size),wanted.getchannel('A'))
            maximum_error=max(maximum_error,max(v[1] for v in diff.getextrema()))
        if maximum_error>9:raise RuntimeError('RGB565 quantization exceeded expected bound')
        staged.append(dict(path=rel,source_sha256=sha(raw),sha256=sha(output),frames=len(frames),
                           maximum_rgb565_error=maximum_error,qwen_manifest_sha256=sha((PACK/rel/'sprite.json').read_bytes())))
    backup.mkdir()
    for row in staged:
        saved=backup/row['path'];saved.parent.mkdir(parents=True,exist_ok=True)
        saved.write_bytes((LAB/row['path']).read_bytes());(LAB/row['path']).write_bytes((temp/row['path']).read_bytes())
    report=dict(status='staged-requires-paired-game-verification',revision=2,
                coverage='exact original nearest 2x',optional_masks='omitted; source offsets are not reusable',files=staged)
    (BASE/'grimoire-sprites-stage-r2.json').write_text(json.dumps(report,indent=2)+'\n')
    (BASE/'grimoire-sprites-stage.json').write_text(json.dumps(report,indent=2)+'\n')
    manifest=json.loads((BASE/'manifest.json').read_text())
    for row in staged:manifest['files']['game-wide169/'+row['path']]=row['sha256']
    (BASE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':stage()
