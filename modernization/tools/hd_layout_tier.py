"""Stage a third 1920x1440 UI layout tier beside the existing two tiers.

This only generates candidate CFG files under the ignored HD workspace. The
community executable has no proven Rect3 or 1920x1440 key reader, so these
files must not be copied into the installed game yet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

RECT = re.compile(rb"^(?P<indent>[ \t]*)Rect2[ \t]*=[ \t]*(?P<values>-?\d+[ \t]*,[ \t]*-?\d+[ \t]*,[ \t]*-?\d+[ \t]*,[ \t]*-?\d+)")
COORD = re.compile(rb"^(?P<indent>[ \t]*)800x600_(?P<name>[A-Za-z0-9_]+)[ \t]*=[ \t]*(?P<value>-?\d+)")


def scaled(value: int) -> int:
    return (value * 12 + 2) // 5 if value >= 0 else -((-value * 12 + 2) // 5)


def convert(data: bytes) -> tuple[bytes, int, int]:
    output = []
    rectangles = coordinates = 0
    for line in data.splitlines(keepends=True):
        output.append(line)
        newline = b"\r\n" if line.endswith(b"\r\n") else b"\n"
        rect = RECT.match(line)
        if rect:
            values = [int(part.strip()) for part in rect.group("values").split(b",")]
            output.append(rect.group("indent") + b"Rect3=" + b",".join(str(scaled(v)).encode() for v in values)
                          + b"  ; staged 1920x1440 tier" + newline)
            rectangles += 1
            continue
        coord = COORD.match(line)
        if coord:
            output.append(coord.group("indent") + b"1920x1440_" + coord.group("name") + b"="
                          + str(scaled(int(coord.group("value")))).encode()
                          + b"  ; staged HD tier" + newline)
            coordinates += 1
    return b"".join(output), rectangles, coordinates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("modernization/assets/hd/config-1920x1440"))
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    manifest = {"status": "candidate-only-not-installed", "tier": [1920, 1440],
                "factor": 2.4, "files": []}
    for source in sorted((root / "Interface").rglob("*.cfg")):
        raw = source.read_bytes()
        candidate, rectangles, coordinates = convert(raw)
        if not rectangles and not coordinates:
            continue
        relative = source.relative_to(root)
        output = args.out / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(candidate)
        manifest["files"].append({
            "source": relative.as_posix(),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "output_sha256": hashlib.sha256(candidate).hexdigest(),
            "rect3": rectangles, "coordinates_1920x1440": coordinates,
        })
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Staged %d CFG files: %d Rect3, %d named coordinates" %
          (len(manifest["files"]), sum(f["rect3"] for f in manifest["files"]),
           sum(f["coordinates_1920x1440"] for f in manifest["files"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
