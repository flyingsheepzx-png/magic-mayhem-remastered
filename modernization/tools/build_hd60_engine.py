"""Compose the hash-verified final HD engine with the accepted 600 search limit."""
import argparse
import hashlib
import json
from pathlib import Path

import pefile


ROOT = (Path(__file__).resolve().parents[2] / "game")
ORIGINAL = ROOT / "Chaos.exe"
OUTPUT = ROOT / "modernization/build/Chaos-HD60-engine.exe"
ORIGINAL_SHA = "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"
HD_SHA = "b6af9fd3969e4cc985495e858d7da2c66ec29c95b50343d89bc2c5575472a117"
ROUTE_SITE = 0x4E5543
ROUTE_OLD = bytes.fromhex("e85c700b00")
ROUTE_NEW = bytes.fromhex("b858020000")
RUNTIME_SITES = {
    0x50FCEC: bytes.fromhex("8b8ee8060000"),
    0x5106DA: bytes.fromhex("8b955f0b0000"),
    0x512460: bytes.fromhex("83ec4053558be9"),
    0x4FA261: bytes.fromhex("8b463103cd"),
    0x4FA622: bytes.fromhex("8b4c241c89842480000000"),
    0x4FFF41: bytes.fromhex("8b41085e48"),
    0x5108C9: bytes.fromhex("8b8d830b0000"),
    0x4FD552: bytes.fromhex("8bcde8472d0000"),
    0x4FD5A6: bytes.fromhex("50ff9180000000"),
    0x5104D1: bytes.fromhex("8b85630b0000"),
    0x46B488: bytes.fromhex("a130486c008b0d141f6e00"),
    0x4E3E5B: bytes.fromhex("8b3564515c00"),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hd_exe", type=Path)
    args = parser.parse_args()
    original, hd = ORIGINAL.read_bytes(), args.hd_exe.read_bytes()
    if digest(original) != ORIGINAL_SHA or digest(hd) != HD_SHA:
        raise RuntimeError("Unknown original or final HD engine; composition refused")
    if len(original) != len(hd):
        raise RuntimeError("HD engine file layout differs from original")
    pe = pefile.PE(data=original)
    if pe.OPTIONAL_HEADER.ImageBase != 0x400000:
        raise RuntimeError("Unexpected image base")
    site = pe.get_offset_from_rva(ROUTE_SITE - pe.OPTIONAL_HEADER.ImageBase)
    if original[site:site+5] != ROUTE_OLD or hd[site:site+5] != ROUTE_OLD:
        raise RuntimeError("600 search site conflicts with HD edits")
    for va, expected in RUNTIME_SITES.items():
        offset = pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)
        if original[offset:offset+len(expected)] != expected or hd[offset:offset+len(expected)] != expected:
            raise RuntimeError(f"Runtime hook conflict at {va:#x}")
    composed = bytearray(hd)
    composed[site:site+5] = ROUTE_NEW
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists() and OUTPUT.read_bytes() != composed:
        raise RuntimeError("Existing combined engine differs; preserve it before rebuilding")
    OUTPUT.write_bytes(composed)
    result = {"target": str(OUTPUT), "sha256": digest(composed),
              "original_sha256": ORIGINAL_SHA, "hd_sha256": HD_SHA,
              "route_va": hex(ROUTE_SITE), "route_limit": 600,
              "runtime_sites_verified": len(RUNTIME_SITES)}
    (OUTPUT.with_suffix(".json")).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
