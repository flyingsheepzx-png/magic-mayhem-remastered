"""Offline compiled budget hook + original native minimum/output capacity guard."""
import json
import struct
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import (UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EBX,
    UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP)
from install_search_budget import installer as i

def main():
    path=i.ROOT/'game-wide169/Chaos-Wide169-engine.exe'
    assert i.sha(path)==i.ENGINE
    engine=pefile.PE(str(path));dll=pefile.PE(str(i.BUILD/'repath.dll'))
    base=dll.OPTIONAL_HEADER.ImageBase
    lines=(i.BUILD/'repath.map').read_text().splitlines()
    def sym(name):return int(next(x for x in lines if name in x).split()[2],16)
    def vm():
        u=Uc(UC_ARCH_X86,UC_MODE_32)
        u.mem_map(0x400000,0x400000);u.mem_write(0x400000,engine.get_memory_mapped_image())
        u.mem_map(base,(dll.OPTIONAL_HEADER.SizeOfImage+4095)&~4095)
        u.mem_write(base,dll.get_memory_mapped_image())
        u.mem_map(0x2000000,0x10000);u.reg_write(UC_X86_REG_ESP,0x2008000)
        return u
    def w(u,a,v):u.mem_write(a,struct.pack('<i',v))
    def r(u,a):return struct.unpack('<i',u.mem_read(a,4))[0]
    regs=(UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,
          UC_X86_REG_EDI,UC_X86_REG_EBP)
    cases=0
    for players in (1,2):
        for original in (0,1,70,210):
            for shared in (0,53,601):
                u=vm();w(u,0x6e1f0c,players);w(u,0x6df188,shared);w(u,0x6df18c,original)
                for n,reg in enumerate(regs):u.reg_write(reg,0x123400+n)
                # v27 entry detour establishes the independent shared allowance.
                u.emu_start(sym('?request_hook@@'),0x5128a6,count=50)
                expected_shared=601 if players==1 else shared
                assert r(u,0x6df188)==expected_shared
                u.emu_start(sym('?budget_hook@@'),0x513168,count=50)
                assert u.reg_read(UC_X86_REG_ESP)==0x2008000-0x2ac
                assert all(u.reg_read(reg)==0x123400+n for n,reg in enumerate(regs))
                expected_request=600 if players==1 else original
                assert r(u,0x6df18c)==expected_request
                # Execute unmodified native min(shared,remaining) instructions.
                u.emu_start(0x513168,0x513173,count=10)
                assert u.reg_read(UC_X86_REG_ESI)==min(expected_shared,expected_request)
                if players==1:
                    # Worst-case full allowance leaves one shared unit; no yield.
                    assert expected_shared-expected_request==1
                cases+=1
    for count in (0,15,16,17,600):
        u=vm();u.reg_write(UC_X86_REG_EBP,0x2001000);w(u,0x2001010,count)
        u.emu_start(0x54bd5b,0x54bd65 if count<16 else 0x54be34,count=5)
        cases+=1
    report=dict(result='passed',cases=cases,dll_sha256=i.sha(i.BUILD/'repath.dll'),
                coverage='compiled single/multiplayer budgets, native minimum and 16-waypoint guard; not route-quality acceptance',
                gameplay_tested=False)
    i.write(i.BUILD/'budget-verification.json',report);print(json.dumps(report))

if __name__=='__main__':main()
