"""Read-only, bounded control-flow inspection of the known community executable.

Follow instruction boundaries from an explicit entry; report unresolved edges
instead of treating embedded data or a guessed signature as executable code.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_GRP_JUMP, CS_GRP_RET
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

ROOT = (Path(__file__).resolve().parents[2] / "game")
SUPPORTED = "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"


def inspect(data, base, entry, end, imports=None):
    if not base <= entry < end <= base + len(data):
        raise ValueError("Invalid inspection range")
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    pending = [entry]
    decoded = {}
    owners = {}
    unresolved = []
    while pending:
        address = pending.pop()
        while entry <= address < end:
            if address in decoded:
                break
            if address in owners:
                raise ValueError(f"Branch enters an instruction at {address:08x}")
            ins = next(md.disasm(data[address-base:min(end-base, address-base+15)], address, count=1), None)
            if ins is None:
                unresolved.append({"site": address, "reason": "undecodable"})
                break
            if any(byte in owners for byte in range(address, address + ins.size)):
                raise ValueError(f"Overlapping instructions at {address:08x}")
            refs = [op.mem.disp for op in ins.operands if op.type == X86_OP_MEM
                    and not op.mem.base and not op.mem.index]
            record = {"address": address, "bytes": ins.bytes.hex(), "mnemonic": ins.mnemonic,
                      "operands": ins.op_str, "absolute_memory": refs}
            if ins.mnemonic == "call":
                record["call_target"] = ins.operands[0].imm if ins.operands[0].type == X86_OP_IMM else None
                record["import"] = (imports or {}).get(refs[0]) if refs else None
            decoded[address] = record
            for byte in range(address, address + ins.size):
                owners[byte] = address
            if ins.group(CS_GRP_RET) or ins.mnemonic in ("int3", "ud2"):
                break
            if ins.group(CS_GRP_JUMP):
                if ins.operands[0].type == X86_OP_IMM:
                    target = ins.operands[0].imm
                    record["branch_target"] = target
                    if entry <= target < end:
                        pending.append(target)
                    else:
                        unresolved.append({"site": address, "target": target, "reason": "outside range"})
                else:
                    unresolved.append({"site": address, "reason": "indirect branch"})
                if ins.mnemonic == "jmp":
                    break
            address += ins.size
        else:
            unresolved.append({"site": address, "reason": "range end fallthrough"})
    return {"entry": entry, "end": end, "instructions": [decoded[a] for a in sorted(decoded)],
            "unresolved_edges": unresolved, "runtime_semantics_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", type=lambda s: int(s, 0))
    parser.add_argument("end", type=lambda s: int(s, 0))
    parser.add_argument("--exe", type=Path, default=ROOT / "Chaos.exe")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--calls-only", action="store_true")
    args = parser.parse_args()
    digest = hashlib.sha256(args.exe.read_bytes()).hexdigest()
    if digest != SUPPORTED:
        raise SystemExit("Unsupported executable hash; address inspection refused")
    pe = pefile.PE(str(args.exe))
    imports = {item.address: item.name.decode("ascii") if item.name else f"ordinal:{item.ordinal}"
               for dll in pe.DIRECTORY_ENTRY_IMPORT for item in dll.imports}
    result = inspect(pe.get_memory_mapped_image(), pe.OPTIONAL_HEADER.ImageBase,
                     args.entry, args.end, imports)
    result["exe_sha256"] = digest
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    for row in result["instructions"]:
        if not args.calls_only or row["mnemonic"] == "call":
            print(f'{row["address"]:08x} {row["mnemonic"]:<8} {row["operands"]}'
                  + (f' [{row["import"]}]' if row.get("import") else ""))
    print("Unresolved edges:", json.dumps(result["unresolved_edges"]))


if __name__ == "__main__":
    main()
