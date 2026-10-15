"""Read-only x86 disassembly of selected ranges in the verified community build."""
import argparse
import hashlib
from pathlib import Path

import capstone
import pefile

ROOT = (Path(__file__).resolve().parents[2] / "game")
SUPPORTED = "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("start", type=lambda value: int(value, 0))
    parser.add_argument("length", type=lambda value: int(value, 0))
    args = parser.parse_args()
    path = ROOT / "Chaos.exe"
    if hashlib.sha256(path.read_bytes()).hexdigest() != SUPPORTED:
        raise SystemExit("Unknown executable hash")
    pe = pefile.PE(str(path))
    code = pe.get_data(args.start - pe.OPTIONAL_HEADER.ImageBase, args.length)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    for insn in decoder.disasm(code, args.start):
        print(f"{insn.address:08x}  {insn.bytes.hex():<20} {insn.mnemonic:<7} {insn.op_str}")


if __name__ == "__main__":
    main()
