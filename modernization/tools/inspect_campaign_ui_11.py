"""Read-only disassembly/string references on the identified 1.1 disk engine."""
from pathlib import Path
import argparse,hashlib,struct
import pefile,capstone

ROOT=Path(__file__).resolve().parents[2]
ENGINE=ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Chaos-Wide169-engine.exe'
SHA='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'

def main():
 p=argparse.ArgumentParser();p.add_argument('--range',nargs=2,type=lambda x:int(x,0));p.add_argument('--string');p.add_argument('--ints',nargs=2,type=lambda x:int(x,0));a=p.parse_args()
 raw=ENGINE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
 pe=pefile.PE(data=raw);data=pe.get_memory_mapped_image();base=pe.OPTIONAL_HEADER.ImageBase
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 if a.ints:print(struct.unpack_from('<'+str(a.ints[1])+'i',data,a.ints[0]-base))
 if a.range:
  for i in md.disasm(data[a.range[0]-base:a.range[1]-base],a.range[0]):print(f'{i.address:08x} {i.bytes.hex():20s} {i.mnemonic:7s} {i.op_str}')
 if a.string:
  start=0
  while True:
   pos=data.lower().find(a.string.encode().lower(),start)
   if pos<0:break
   string_start=data.rfind(b'\0',0,pos)+1
   print('STRING',hex(base+string_start),data[string_start:data.find(b'\0',pos)].decode('ascii','replace'))
   ref=0;target=struct.pack('<I',base+string_start)
   while True:
    ref=data.find(target,ref)
    if ref<0:break
    print('REF',hex(base+ref));ref+=4
   start=pos+1

if __name__=='__main__':main()
