"""Recover native AI configuration bindings; read-only runtime, hash-gated input."""
import argparse,hashlib,json,re,struct
from pathlib import Path
import pefile
ROOT=Path(__file__).resolve().parents[2]
SHA='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'

def recover(exports,engine,config):
    raw=engine.read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
    pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase;image=pe.get_memory_mapped_image()
    text=(exports/'00407f60.c').read_text()
    pattern=r'GetPrivateProfileStringA\s*\(.*?s_([A-Z0-9_]+)_([0-9a-f]{8}).*?FUN_0059bc22\s*\([^;]*?&DAT_([0-9a-f]{8}),&DAT_([0-9a-f]{8})\);'
    values={}
    for line in config.read_text(encoding='latin1').splitlines():
        line=line.split(';')[0].strip()
        if '=' in line:
            key,value=line.split('=',1);values[key.strip().upper()]=value.strip()
    rows=[]
    for name,string,threshold,scale in re.findall(pattern,text,re.S):
        va=int(string,16);end=image.index(b'\0',va-base)
        native=image[va-base:end].decode('ascii');assert native==name
        t,s=int(threshold,16),int(scale,16)
        offset=(t-0x5f8264)//4
        rows.append(dict(key=name,string_va=hex(va),threshold_va=hex(t),scale_va=hex(s),parameter_slot=offset,
          configured=values.get(name),state='assigned' if values.get(name) else 'native_default_retained',
          disk_threshold=struct.unpack_from('<f',image,t-base)[0] if t-base+4<len(image) else None,
          disk_scale=struct.unpack_from('<f',image,s-base)[0] if s-base+4<len(image) else None))
    assert len(rows)>100 and len({r['key'] for r in rows})==len(rows)
    unused=[dict(key=k,value=v) for k,v in values.items() if k not in {r['key'] for r in rows}]
    return dict(engine_sha256=SHA,parser_va='0x407f60',rows=rows,unused_config_keys=unused,
      note='parameter_slot is threshold-array position, NOT action feature-vector index; zero disk defaults may be initialized later')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--exports',type=Path,default=Path('D:/Tools/magic-mayhem-re/projects/ai-review-20261001/functions'))
    p.add_argument('--engine',type=Path,default=ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Chaos-Wide169-engine.exe')
    p.add_argument('--config',type=Path,default=Path('D:/Games/Magic&Mayham_Remastered_1.1/runtime/CFG/ai.cfg'))
    p.add_argument('--output',type=Path);a=p.parse_args();result=recover(a.exports,a.engine,a.config)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(bindings=len(result['rows']),assigned=sum(r['state']=='assigned' for r in result['rows']),unused_config_keys=result['unused_config_keys']),indent=2))
