"""Offline x86 execution of the built scheduler detour; never launches the game."""
import json
import re
import struct

import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import (UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EBX,
    UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP)
from install_path_review import BUILD, ROOT, ENGINE, sha


def verify():
    engine = ROOT/'game-wide169/Chaos-Wide169-engine.exe'
    assert sha(engine) == ENGINE
    original = pefile.PE(str(engine))
    dll = pefile.PE(str(BUILD/'repath.dll'))
    address = int(re.search(r'\?request_hook@@YAXXZ\s+([0-9a-fA-F]+)',
                           (BUILD/'repath.map').read_text()).group(1), 16)
    regs = (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
            UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP)
    cases = 0
    for players in (1, 2):
        for budget in (-200, 0, 1, 600):
            u = Uc(UC_ARCH_X86, UC_MODE_32)
            u.mem_map(0x400000, 0x400000)
            u.mem_write(0x400000, original.get_memory_mapped_image())
            base = dll.OPTIONAL_HEADER.ImageBase
            size = (dll.OPTIONAL_HEADER.SizeOfImage+4095)&~4095
            u.mem_map(base, size)
            u.mem_write(base, dll.get_memory_mapped_image())
            u.mem_map(0x2000000, 0x10000)
            u.reg_write(UC_X86_REG_ESP, 0x2008000)
            for i, reg in enumerate(regs): u.reg_write(reg, 0x123400+i)
            u.mem_write(0x6e1f0c, struct.pack('<i', players))
            u.mem_write(0x6df188, struct.pack('<i', budget))
            u.emu_start(address, 0x5128a6, count=50)
            result = struct.unpack('<i', u.mem_read(0x6df188, 4))[0]
            assert result == (601 if players == 1 else budget)
            assert u.reg_read(UC_X86_REG_ESP) == 0x2008000-0x2ac
            assert all(u.reg_read(reg) == 0x123400+i for i, reg in enumerate(regs))
            # Native 70/210 request bounds can never exhaust the new shared
            # allowance. Exact exhaustion used to delay even a found route.
            if players == 1:
                for consumed in (0, 70, 210): assert result-consumed > 0
            cases += 1
    report = dict(cases=cases, dll_sha256=sha(BUILD/'repath.dll'),
                  result='passed', gameplay_tested=False)
    (BUILD/'hook-verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    verify()
