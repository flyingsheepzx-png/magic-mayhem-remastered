"""Center the 640x360 FMV rectangle in the verified Wide169 engine."""

import argparse
import hashlib
import struct
from pathlib import Path

import pefile


EXPECTED_SHA256 = "1d2df6135238dec69f6ec74280440a06b43c66353c886f42633f4143d710b16f"
EXPECTED_LAUNCHER_SHA256 = "01119a189bfd50d3fed7a07d436be66dd02d93266dd259206084b34102c35bc0"
# The menu intro and realm FMV paths each load these two high-resolution offsets.
# Both were (80, 120), the center of the original 800x600 display.
OFFSETS = {0x5C6FB8: 320, 0x5C6FBC: 180, 0x5C7588: 320, 0x5C758C: 180}
OLD = {0x5C6FB8: 80, 0x5C6FBC: 120, 0x5C7588: 80, 0x5C758C: 120}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def patch(source: Path, destination: Path):
    data = bytearray(source.read_bytes())
    if sha(data) != EXPECTED_SHA256:
        raise ValueError("Unknown Wide169 engine; refusing address patch")
    pe = pefile.PE(data=bytes(data))
    if pe.OPTIONAL_HEADER.ImageBase != 0x400000:
        raise ValueError("Unexpected PE image base")
    for va, value in OFFSETS.items():
        offset = pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)
        before = struct.unpack_from("<I", data, offset)[0]
        if before != OLD[va]:
            raise ValueError(f"Unexpected data at {va:#x}: {before}")
        struct.pack_into("<I", data, offset, value)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return sha(data)


def patch_launcher(source: Path, destination: Path, engine_sha256: str):
    data = source.read_bytes()
    if sha(data) != EXPECTED_LAUNCHER_SHA256:
        raise ValueError("Unknown Wide169 launcher")
    old = EXPECTED_SHA256.encode("utf-16le")
    if data.count(old) != 1 or len(engine_sha256) != 64:
        raise ValueError("Expected engine hash literal is not unique")
    patched = data.replace(old, engine_sha256.encode("utf-16le"))
    destination.write_bytes(patched)
    return sha(patched)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--launcher", action="store_true")
    parser.add_argument("--engine-sha256")
    args = parser.parse_args()
    if args.launcher:
        if not args.engine_sha256:
            parser.error("--launcher requires --engine-sha256")
        print(patch_launcher(args.source, args.destination, args.engine_sha256))
    else:
        print(patch(args.source, args.destination))
