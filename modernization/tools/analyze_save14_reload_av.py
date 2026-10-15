"""Read the captured first AV's full minidump, without a game process."""
import mmap,struct,json
from pathlib import Path
import build_11_reload_surface as b
def main():
 root=b.b.ROOT/'modernization/logs/remastered-ui/save14-reload-before-v4/exception'
 with (root/'av-1.dmp').open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  count,directory=struct.unpack_from('<II',raw,8);streams={}
  for i in range(count):
   typ,size,rva=struct.unpack_from('<III',raw,directory+12*i);streams[typ]=(size,rva)
  start=streams[9][1];n,offset=struct.unpack_from('<QQ',raw,start);regions=[]
  for i in range(n):
   base,size=struct.unpack_from('<QQ',raw,start+16+16*i);regions.append((base,size,offset));offset+=size
  def read(address,size):
   return next(bytes(raw[offset+address-base:offset+address-base+size]) for base,length,offset in regions if base<=address and address+size<=base+length)
  event=next(json.loads(x) for x in (root/'events.jsonl').read_text().splitlines() if json.loads(x).get('av')==1)
  obj=int(event['esi'],16);header=struct.unpack('<12I',read(obj,48))
  n=struct.unpack('<I',read(0x6f8154,4))[0];table=struct.unpack('<'+'I'*n,read(0x6f6950,n*4))
  assert header[1]==0 and header[2]!=0 and table.count(obj)==1 and header[7]==table.index(obj)
  stack=struct.unpack('<24I',read(int(event['esp'],16),96))
  assert 0x4d38a4 in stack
  result=dict(engine_sha256=b.b.sha(b.base.DEST/'runtime/Chaos-Wide169-engine.exe'),event=event,object_address=hex(obj),object_header=[hex(x) for x in header],registry_count=n,registry_index=table.index(obj),stack_words=[hex(x) for x in stack],native_fault='58b40b dereferences EAX loaded from object+4; queried interface object+8 remains nonnull',native_creation_caller='4d3840 calls58ad90 with surface at control+29; return4d38a4',scope='Captured first-chance memory, not stale shutdown stack speculation')
 b.base.write(root/'root-cause.json',result);print('First AV object ownership and native creation caller verified')
if __name__=='__main__':main()
