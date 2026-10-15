"""Scale verified realm ANI v5 placement offsets for 2x flag art."""
import hashlib
import json
import struct
from stage_mixed_ui_v4_portmanteau_sprites import BASE, LAB

REL='Interface/RealmViewer/Generic/flags.ani'
SOURCE='4d159b3927591f4caf0b82e9cec5cb6a1676f64b6a906b16a1f19dc604d8f773'

def stage():
    path=LAB/REL;raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE:raise RuntimeError('Unknown flag ANI')
    magic,length,count,version,reserved,sequences=struct.unpack_from('<6I',raw)
    start=44+sequences*4
    if raw[:4]!=b'ANI\0' or length!=len(raw) or version!=5 or reserved!=0 or start+count*44!=len(raw):
        raise RuntimeError('Unknown ANI v5 record layout')
    output=bytearray(raw)
    for i in range(count):
        x,y=struct.unpack_from('<ii',raw,start+i*44+8)
        if abs(x)>100 or abs(y)>100:raise RuntimeError('Unexpected placement offset')
        struct.pack_into('<ii',output,start+i*44+8,x*2,y*2)
    backup=BASE/'before-realm-flag-offsets';saved=backup/REL
    if backup.exists():raise RuntimeError('Offset backup already exists')
    manifest_path=BASE/'manifest.json';manifest_raw=manifest_path.read_bytes();manifest=json.loads(manifest_raw)
    if manifest['files'].get('game-wide169/'+REL,SOURCE)!=SOURCE:raise RuntimeError('ANI manifest differs')
    saved.parent.mkdir(parents=True);saved.write_bytes(raw)
    (backup/'manifest.json').write_bytes(manifest_raw)
    digest=hashlib.sha256(output).hexdigest()
    try:
        path.write_bytes(output);manifest['files']['game-wide169/'+REL]=digest
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    except Exception:
        path.write_bytes(raw);manifest_path.write_bytes(manifest_raw);raise
    report={'status':'staged-awaiting-paired-retest','source_sha256':SOURCE,'sha256':digest,
            'records':count,'sequences':sequences,'changed_fields':'signed x/y at +8/+12 in 44-byte v5 records',
            'preserved':'header, sequence table, frames, timing and all other bytes','rollback':str(saved)}
    (BASE/'realm-flag-offsets-stage.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':stage()
