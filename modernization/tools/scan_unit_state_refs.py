"""Find x86 instructions referring to candidate unit fields in known build."""
import argparse
import hashlib
from pathlib import Path

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

ROOT = (Path(__file__).resolve().parents[2] / "game")
SHA = "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("field", nargs="+", type=lambda x: int(x, 0))
    ap.add_argument("--calls", action="store_true", help="Treat arguments as direct call targets")
    args = ap.parse_args()
    path = ROOT / "Chaos.exe"
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA:
        raise SystemExit("Unknown executable")
    pe = pefile.PE(str(path))
    image = pe.get_memory_mapped_image()
    base = pe.OPTIONAL_HEADER.ImageBase
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    for section in pe.sections:
        if not section.Characteristics & 0x20000000:
            continue
        start = section.VirtualAddress
        end = start + section.Misc_VirtualSize
        rva = start
        while rva < end:
            ins = next(md.disasm(image[rva:rva + 15], base + rva, count=1), None)
            if ins is None:
                rva += 1
                continue
            if ((args.calls and ins.mnemonic == "call" and ins.operands
                 and getattr(ins.operands[0], "imm", None) in args.field) or
                (not args.calls and any(op.type == X86_OP_MEM and op.mem.disp in args.field
                                        for op in ins.operands))):
                print(f"{ins.address:08x} {ins.mnemonic:8} {ins.op_str}")
            rva += ins.size


if __name__ == "__main__":
    main()
