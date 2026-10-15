"""Build and verify an opt-in known-build executable with route limit 600.

The community Chaos.exe remains byte-for-byte original for ordinary launches.
The generated sibling executable uses the same installed assets and can be
removed to roll back. Only the second positive-config atoi call is replaced;
its following stack cleanup and global store are unchanged.
"""
from pathlib import Path
import argparse
import hashlib
import json

import pefile

ROOT = (Path(__file__).resolve().parents[2] / "game")
SOURCE = ROOT / "Chaos.exe"
TARGET = ROOT / "Chaos-singleplayer-600.exe"
BASE_SHA256 = "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"
SITE_VA = 0x4E5543
OLD = bytes.fromhex("e85c700b00")  # call atoi, followed by add esp,4
NEW = bytes.fromhex("b858020000")  # mov eax,600, followed by add esp,4


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_image() -> tuple[bytes, int]:
    original = SOURCE.read_bytes()
    if sha256(original) != BASE_SHA256:
        raise RuntimeError("Unsupported community executable; route build refused")
    pe = pefile.PE(data=original)
    offset = pe.get_offset_from_rva(SITE_VA - pe.OPTIONAL_HEADER.ImageBase)
    if original[offset:offset + len(OLD)] != OLD:
        raise RuntimeError("Unexpected route-limit loader bytes; build refused")
    patched = bytearray(original)
    patched[offset:offset + len(NEW)] = NEW
    return bytes(patched), offset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "verify", "rollback"))
    args = parser.parse_args()
    image, offset = expected_image()
    expected = sha256(image)
    if args.action == "install":
        if TARGET.exists() and TARGET.read_bytes() != image:
            raise RuntimeError("Existing opt-in executable differs; refusing overwrite")
        if not TARGET.exists():
            temporary = TARGET.with_suffix(".exe.tmp")
            temporary.write_bytes(image)
            if sha256(temporary.read_bytes()) != expected:
                raise RuntimeError("Staged executable failed hash check")
            temporary.replace(TARGET)
    elif args.action == "rollback":
        if TARGET.exists():
            if sha256(TARGET.read_bytes()) != expected:
                raise RuntimeError("Opt-in executable changed; refusing removal")
            TARGET.unlink()
    if args.action != "rollback" and sha256(TARGET.read_bytes()) != expected:
        raise RuntimeError("Opt-in executable failed final hash check")
    print(json.dumps({"action": args.action, "source": str(SOURCE),
                      "source_sha256": BASE_SHA256, "target": str(TARGET),
                      "target_sha256": expected, "patch_va": hex(SITE_VA),
                      "patch_file_offset": offset, "limit": 600,
                      "original_unchanged": sha256(SOURCE.read_bytes()) == BASE_SHA256,
                      "opt_in": True, "multiplayer_validated": False}, indent=2))


if __name__ == "__main__":
    main()
