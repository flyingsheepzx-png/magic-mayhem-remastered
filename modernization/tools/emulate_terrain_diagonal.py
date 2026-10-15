"""Execute hash-gated native terrain functions offline against captured cells."""
from pathlib import Path
import hashlib,struct,json
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EAX

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'modernization/logs/wide169/1790700149365547600'

class Native:
    def __init__(self):
        exe=ROOT/'game-wide169/Chaos-Wide169-engine.exe'
        assert hashlib.sha256(exe.read_bytes()).hexdigest()=='43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d'
        p=pefile.PE(str(exe));self.u=Uc(UC_ARCH_X86,UC_MODE_32);self.u.mem_map(0x400000,0x400000)
        self.u.mem_write(0x400000,p.get_memory_mapped_image())
        for a,n in [(0x1000000,0x200000),(0x1400000,0x100000),(0x1800000,0x100000),(0x2000000,0x100000)]:self.u.mem_map(a,n)
        self.u.mem_write(0x1000000,(RUN/'map.bin').read_bytes());self.u.mem_write(0x1400000,(RUN/'tile-types.bin').read_bytes())
        self.w(0x6c5494,80);self.w(0x6c5498,80);self.w(0x6c549c,25);self.w(0x6c54a0,6400)
        self.w(0x6c54dc,0x1000000);self.w(0x65660c,0x1400000);self.w(0x5e1780,25);self.w(0x6c5c80,0)
        for i in range(80):self.w(0x6cb942+4*i,80*i)
        for i in range(25):self.w(0x6cb8c2+4*i,6400*i)
        self.profile=0x1800000;self.set_profile(4,1)
    def w(self,a,v):self.u.mem_write(a,struct.pack('<I',v&0xffffffff))
    def set_profile(self,height,width,mode=1):self.u.mem_write(self.profile,struct.pack('<4iBiB',height,width,0,mode,0,0,0))
    def call(self,address,args,ecx=0x6c5490):
        self.u.mem_write(0x20ff000,struct.pack('<'+'I'*(len(args)+1),0x20fe000,*[a&0xffffffff for a in args]))
        self.u.reg_write(UC_X86_REG_ESP,0x20ff000);self.u.reg_write(UC_X86_REG_ECX,ecx)
        self.u.emu_start(address,0x20fe000,count=100000)
        return self.u.reg_read(UC_X86_REG_EAX)
    def edge(self,a,b):
        result=self.call(0x4f3990,[*a,*b,self.profile,0x1800100,-1])
        return [result,struct.unpack('<i',self.u.mem_read(0x1800100,4))[0]]
    def patch(self,dll=None):
        p=pefile.PE(str(dll or ROOT/'modernization/build/terrain-diagonal-v1/terrain_diagonal.dll'))
        base=p.OPTIONAL_HEADER.ImageBase
        self.u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095)
        self.u.mem_write(base,p.get_memory_mapped_image())
        target=base+next(s.address for s in p.DIRECTORY_ENTRY_EXPORT.symbols if s.name==b'terrain_hook')
        self.u.mem_write(0x4f3fff,b'\xe9'+struct.pack('<i',target-0x4f4004)+b'\x90'*5)

def main():
    n=Native(); n.patch(); results=[]
    for size in [1,2]:
        for h in [1,2,4,6,8]:
            n.set_profile(h,size)
            results.append(dict(width=size,height=h,start=n.edge((58,78,4),(57,77,4)),
             portal=n.edge((54,74,5),(53,73,5)),
             climb=n.edge((54,74,5),(54,73,6)),descend=n.edge((54,73,6),(53,73,5))))
    print(json.dumps(results,indent=2))
    (ROOT/'modernization/logs/terrain-native-emulation.json').write_text(json.dumps(results,indent=2))

if __name__=='__main__':main()
