"""Enlarge only the Portmanteau colour ring frames in shared SplIcons.spr."""
import hashlib
import json
import struct
from PIL import Image, ImageChops
from compare_hd_baseline import baseline_identity
from spr_assets import read_spr, decode
from stage_mixed_ui_v3_sprites import encode
from stage_mixed_ui_v4_portmanteau_sprites import BASE, LAB, PACK, sha

REL='Sprites/SplIcons.spr'
RING=range(0,3)

def stage():
    baseline_identity()
    source=LAB/REL
    backup=BASE/'before-colour-buttons'
    if backup.exists() and (backup/'SplIcons.spr').read_bytes()!=source.read_bytes():
        raise RuntimeError('Colour-button backup source mismatch')
    raw=source.read_bytes();palettes,frames=read_spr(source)
    meta_path=PACK/REL/'sprite.json';meta_raw=meta_path.read_bytes();meta=json.loads(meta_raw)
    if palettes or len(frames)!=234 or sha(raw)!=meta['source_sha256'] or not meta['complete'] or meta['scale']!=2:
        raise RuntimeError('Unexpected source or Qwen output')
    records={row['index']:row for row in meta['frames']}
    origin=[min(f['offset'][i] for f in frames if f['width']) for i in range(2)]
    encoded=[];maximum_error=0
    for frame in frames:
        if frame['index'] not in RING:
            encoded.append(frame['data']);continue
        row=records[frame['index']];png=PACK/REL/row['file']
        if (sha(png.read_bytes())!=row['sha256'] or row['source_size']!=[frame['width'],frame['height']]
            or row['offset']!=frame['offset'] or row['flags']!=list(frame['flags'])):
            raise RuntimeError('Frame mismatch: '+str(png))
        with Image.open(png) as opened:
            if list(opened.size)!=meta['target_frame_size']:raise RuntimeError('Wrong Qwen sheet size')
            x,y=[2*(frame['offset'][i]-origin[i]) for i in range(2)]
            image=opened.convert('RGBA').crop((x,y,x+frame['width']*2,y+frame['height']*2))
        image.putalpha(decode(palettes,frame).getchannel('A').resize(image.size,Image.Resampling.NEAREST))
        encoded.append(encode(frame,image))
    output=bytearray(raw[:24]);offset=0
    for data in encoded:output.extend(struct.pack('<I',offset));offset+=len(data)
    for data in encoded:output.extend(data)
    struct.pack_into('<I',output,4,len(output))
    temp=BASE/'sprite-derivatives-colour'/REL;temp.parent.mkdir(parents=True,exist_ok=True);temp.write_bytes(output)
    new_palettes,new_frames=read_spr(temp)
    if new_palettes or len(new_frames)!=len(frames):raise RuntimeError('Roundtrip frame count')
    for old,new in zip(frames,new_frames):
        if old['index'] not in RING:
            if old['data']!=new['data']:raise RuntimeError('Non-ring frame changed')
        else:
            if new['offset']!=[v*2 for v in old['offset']] or new['name']!=old['name']:
                raise RuntimeError('Ring metadata changed')
            original=decode(palettes,old).getchannel('A').resize((old['width']*2,old['height']*2),Image.Resampling.NEAREST)
            if ImageChops.difference(original,decode(new_palettes,new).getchannel('A')).getbbox():
                raise RuntimeError('Ring coverage changed')
    if not backup.exists():
        backup.mkdir();(backup/'SplIcons.spr').write_bytes(raw)
    source.write_bytes(output)
    report=dict(status='staged-requires-paired-game-verification',path=REL,source_sha256=sha(raw),
                sha256=sha(output),frames_preserved=231,frames_enlarged=list(RING),
                qwen_manifest_sha256=sha(meta_raw))
    (BASE/'colour-buttons-stage.json').write_text(json.dumps(report,indent=2)+'\n')
    manifest_path=BASE/'manifest.json';manifest=json.loads(manifest_path.read_text())
    manifest['files']['game-wide169/'+REL]=sha(output)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':stage()
