"""Execute compiled lifecycle detours and cache invalidation offline in x86."""
import json
import struct
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import (UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EBX,
    UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP)
from install_unit_lifecycle import installer as i


def main():
    assert i.sha(i.ROOT/'game-wide169/Chaos-Wide169-engine.exe')==i.ENGINE
    p=pefile.PE(str(i.BUILD/'repath.dll'));base=p.OPTIONAL_HEADER.ImageBase
    lines=(i.BUILD/'repath.map').read_text().splitlines()
    def sym(name):
        return int(next(x for x in lines if name in x).split()[2],16)
    regs=(UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,
          UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP)
    cases=0
    for hook,end,stack_size in [('?reset_hook@@',0x5060a7,8),
                                ('?deserialize_hook@@',0x527316,0x148)]:
        for slot in (0,1,2,-1):
            u=Uc(UC_ARCH_X86,UC_MODE_32)
            u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095)
            u.mem_write(base,p.get_memory_mapped_image())
            u.mem_map(0x400000,0x400000)
            u.mem_map(0x1800000,0x10000);u.mem_map(0x2000000,0x10000)
            pool=0x1800000;unit=pool+slot*0xe4b if slot>=0 else pool+1
            native=b'\xa5'*(3*0xe4b);u.mem_write(pool,native)
            def w(a,n):u.mem_write(a,struct.pack('<I',n))
            w(0x6def58,pool);w(0x6def5c,3)
            w(sym('?unit@@'),unit);u.mem_write(sym('?custom@@'),b'\x01')
            arrays=[(sym('?redirect_states@@'),80),(sym('?actors@@'),96),
                    (sym('?previous@@'),96)]
            for address,size in arrays:u.mem_write(address,b'\x5a'*(3*size))
            flags=[('?ready@@',1),('?captured@@',1),('?command_count@@',4),
                   ('?tags_count@@',4),('?bar_count@@',4)]
            for name,size in flags:u.mem_write(sym(name),b'\x01'*size)
            for n,r in enumerate(regs):u.reg_write(r,unit if r==UC_X86_REG_ECX else 0x123400+n)
            u.reg_write(UC_X86_REG_ESP,0x2008000)
            u.emu_start(sym(hook),end,count=20000)
            assert u.reg_read(UC_X86_REG_ESP)==0x2008000-stack_size
            assert all(u.reg_read(r)==(unit if r==UC_X86_REG_ECX else 0x123400+n) for n,r in enumerate(regs))
            if stack_size==8:
                assert bytes(u.mem_read(0x2008000-8,8))==struct.pack('<II',0x5c241b,0xffffffff)
            for address,size in arrays:
                for n in range(3):
                    assert bytes(u.mem_read(address+n*size,size))==(b'\0' if n==slot else b'\x5a')*size
            for name,size in flags:
                assert bytes(u.mem_read(sym(name),size))==(b'\0' if slot>=0 else b'\x01')*size
            assert bytes(u.mem_read(pool,len(native)))==native
            assert bytes(u.mem_read(sym('?custom@@'),1))==(b'\0' if slot>=0 else b'\x01')
            cases+=1
    report=dict(result='passed',cases=cases,dll_sha256=i.sha(i.BUILD/'repath.dll'),
                checks='target-only reset, replay invalidation, invalid pointer, native bytes unchanged, register/stack ABI',
                gameplay_tested=False)
    i.write(i.BUILD/'lifecycle-verification.json',report);print(json.dumps(report))

if __name__=='__main__':main()
