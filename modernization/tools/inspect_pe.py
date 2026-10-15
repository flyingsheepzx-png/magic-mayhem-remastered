"""Static x86 inspection; dependencies: pefile and capstone."""
import argparse
import re
import struct
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = (Path(__file__).resolve().parents[2] / "game")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default=str(ROOT / "Chaos.exe"))
    ap.add_argument("--refs", nargs="+", type=lambda s: int(s, 0))
    ap.add_argument("--disasm", type=lambda s: int(s, 0))
    ap.add_argument("--length", type=lambda s: int(s, 0), default=256)
    ap.add_argument("--strings", default=None)
    args = ap.parse_args()
    pe = pefile.PE(args.exe)
    base = pe.OPTIONAL_HEADER.ImageBase
    data = pe.get_memory_mapped_image()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    if args.disasm:
        start = args.disasm - base
        for ins in md.disasm(data[start:start+args.length], args.disasm):
            print(f"{ins.address:08x} {ins.bytes.hex():<24} {ins.mnemonic:<8} {ins.op_str}")
    if args.refs:
        for target in args.refs:
            print(f"References to {target:08x}:")
            needle = struct.pack("<I", target)
            for match in re.finditer(re.escape(needle), data):
                rva = match.start()
                print(f" operand/data at {base+rva:08x}")
                start = max(0, rva-16)
                for ins in md.disasm(data[start:rva+24], base+start):
                    print(f" {ins.address:08x} {ins.mnemonic:<8} {ins.op_str}")
    if args.strings:
        pattern = re.compile(args.strings, re.I)
        for match in re.finditer(rb"[ -~]{5,}", data):
            text = match.group().decode("ascii")
            if pattern.search(text):
                print(f"{base+match.start():08x} {text}")

if __name__ == "__main__":
    main()
