"""Build an opt-in battle-surface sizing probe from the verified community EXE.

The default sibling changes only the initial DirectDraw mode and shared
offscreen-surface size. --battle-rect also changes the high-resolution battle
rectangle, which expands the test2 map view. Neither sibling implements native
2K UI or preserves every untested screen; the original executable is untouched.
"""
import hashlib
import json
from pathlib import Path
import struct
import argparse

import pefile

ROOT = (Path(__file__).resolve().parents[2] / "game")
SOURCE = ROOT / "Chaos.exe"
TARGET = ROOT / "Chaos-hd-surface-lab.exe"
RECT_TARGET = ROOT / "Chaos-hd-viewport-rect-lab.exe"
SOURCE_SHA = "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"
PATCHES = {
    0x4E4115: (480, 720),
    0x4E4128: (640, 960),
    0x4E41B2: (640, 960),
    0x4E41D1: (480, 720),
}
RECT_PATCHES = {
    0x5E1728: (800, 1120),
    0x5E172C: (600, 840),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--battle-rect", action="store_true",
                        help="also enlarge the active high-resolution battle rectangle")
    args = parser.parse_args()
    marker = ROOT / "modernization/assets/hd/HD_LAB.json"
    state = json.loads(marker.read_text(encoding="utf-8-sig"))
    if state.get("kind") != "isolated-hd-game-lab" or Path(state["root"]).resolve() != ROOT:
        raise SystemExit("Refusing outside marked HD lab")
    source = SOURCE.read_bytes()
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA:
        raise SystemExit("Unknown executable hash")
    pe = pefile.PE(data=source)
    output = bytearray(source)
    changes = PATCHES | (RECT_PATCHES if args.battle_rect else {})
    for address, (old, new) in changes.items():
        offset = pe.get_offset_from_rva(address - pe.OPTIONAL_HEADER.ImageBase)
        if output[offset:offset + 4] != struct.pack("<I", old):
            raise SystemExit(f"Unexpected bytes at {address:#x}")
        output[offset:offset + 4] = struct.pack("<I", new)
    built = bytes(output)
    target = RECT_TARGET if args.battle_rect else TARGET
    if target.exists() and target.read_bytes() != built:
        raise SystemExit("Existing lab sibling differs; refusing overwrite")
    target.write_bytes(built)
    print(json.dumps({"target": str(target),
                      "sha256": hashlib.sha256(built).hexdigest(),
                      "changes": [{"va": hex(address), "old": old, "new": new}
                                  for address, (old, new) in changes.items()]}, indent=2))


if __name__ == "__main__":
    main()
