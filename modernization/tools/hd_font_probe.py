"""Reversible 2x SFT font experiment for the isolated native UI probe.

SFT v3 stores a 768-byte RGB palette, per-glyph/per-row spacing metrics,
relative frame offsets, and SPR-style run-length encoded glyph frames.  This
tool refuses unknown inputs and writes only the ignored probe runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image

from wide169_build import ROOT


PROBE = ROOT / "modernization/assets/hd/native-ui-2k-probe"
NAMES = (
    "body text 640.sft", "body text 800.sft",
    "heading text 640.sft", "heading text 800.sft",
    "Tooltip Text.sft", "yellowtext.sft",
)
SCALE = 2


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_sft(raw: bytes) -> tuple[bytes, list[tuple[int, int]], list[dict]]:
    if len(raw) < 808 or raw[:4] != b"SFT\0":
        raise ValueError("Not SFT")
    length, version, count, line_height, ascent, descent, palette_count, pixel_format, repeat = struct.unpack_from("<9I", raw, 4)
    if (length != len(raw) or version != 3 or not 0 < count <= 256 or
            not 0 < line_height <= 64 or ascent + descent != line_height or
            palette_count != 0 or pixel_format != 1 or repeat != count):
        raise ValueError("Unknown SFT header")
    palette = raw[40:808]
    metrics_start = 808
    offsets_start = metrics_start + count * line_height * 8
    frames_start = offsets_start + count * 4
    if frames_start > length:
        raise ValueError("Truncated SFT tables")
    metrics = [struct.unpack_from("<2I", raw, metrics_start + i * 8)
               for i in range(count * line_height)]
    offsets = list(struct.unpack_from(f"<{count}I", raw, offsets_start))
    if offsets[0] != 0 or offsets != sorted(set(offsets)):
        raise ValueError("Invalid glyph offsets")
    frames = []
    for i, rel in enumerate(offsets):
        start = frames_start + rel
        end = frames_start + offsets[i + 1] if i + 1 < count else length
        data = raw[start:end]
        if len(data) < 40:
            raise ValueError(f"Truncated glyph {i}")
        size, width, height, x, y = struct.unpack_from("<3I2i", data)
        if size != len(data) or not 0 < width <= 256 or not 0 < height <= 64 or 40 + height * 8 > size:
            raise ValueError(f"Unknown glyph geometry {i}")
        # Text blitter 0x581EC0 indexes a 64-level coverage table with these
        # bytes. The palette is loader metadata; it is not glyph colour.
        im = Image.new("L", (width, height))
        pixels = im.load()
        for row in range(height):
            run_offset, pixel_offset = struct.unpack_from("<2I", data, 40 + row * 8)
            if run_offset < 40 + height * 8 or pixel_offset < 40 + height * 8:
                raise ValueError(f"Invalid glyph row {i}/{row}")
            cursor, position, opaque, paint = run_offset, 0, 0, False
            while position < width:
                if cursor >= size:
                    raise ValueError(f"Truncated glyph run {i}/{row}")
                run = data[cursor]
                cursor += 1
                if position + run > width:
                    raise ValueError(f"Glyph run exceeds width {i}/{row}")
                if paint:
                    if pixel_offset + opaque + run > size:
                        raise ValueError(f"Truncated glyph pixels {i}/{row}")
                    for j in range(run):
                        index = data[pixel_offset + opaque + j]
                        if index > 63:
                            raise ValueError(f"Invalid glyph coverage {i}/{row}: {index}")
                        pixels[position + j, row] = index
                    opaque += run
                position += run
                paint = not paint
        frames.append({"image": im, "x": x, "y": y, "tail": data[20:40]})
    return raw[:40], metrics, frames


def encode_frame(frame: dict) -> bytes:
    source = frame["image"]
    scaled = source.resize((source.width * SCALE, source.height * SCALE), Image.Resampling.LANCZOS)
    coverage = scaled.load()
    width, height = scaled.size
    rows = bytearray(height * 8)
    payload = bytearray()
    for y in range(height):
        runs, pixels = bytearray(), bytearray()
        x, paint = 0, False
        while x < width:
            length = 0
            while x + length < width and (coverage[x + length, y] > 0) == paint:
                length += 1
            if length > 255:
                raise ValueError("Glyph run too wide")
            runs.append(length)
            if paint:
                pixels.extend(min(63, coverage[x + j, y]) for j in range(length))
            x += length
            paint = not paint
        run_offset = 40 + height * 8 + len(payload)
        payload.extend(runs)
        pixel_offset = 40 + height * 8 + len(payload)
        payload.extend(pixels)
        struct.pack_into("<2I", rows, y * 8, run_offset, pixel_offset)
    out = bytearray(40)
    struct.pack_into("<3I2i", out, 0, 40 + len(rows) + len(payload), width, height,
                     frame["x"] * SCALE, frame["y"] * SCALE)
    out[20:40] = frame["tail"]
    return bytes(out + rows + payload)


def scale_sft(raw: bytes) -> bytes:
    header, metrics, frames = read_sft(raw)
    count, line_height = struct.unpack_from("<2I", header, 12)
    palette = raw[40:808]
    result = bytearray(header)
    for offset in (16, 20, 24):
        struct.pack_into("<I", result, offset, struct.unpack_from("<I", result, offset)[0] * SCALE)
    result.extend(palette)
    for i in range(count):
        for row in range(line_height):
            left, right = metrics[i * line_height + row]
            for _ in range(SCALE):
                result.extend(struct.pack("<2I", left * SCALE, right * SCALE))
    encoded = [encode_frame(frame) for frame in frames]
    relative = 0
    for frame in encoded:
        result.extend(struct.pack("<I", relative))
        relative += len(frame)
    for frame in encoded:
        result.extend(frame)
    struct.pack_into("<I", result, 4, len(result))
    parsed_header, parsed_metrics, parsed_frames = read_sft(bytes(result))
    if len(parsed_frames) != count or len(parsed_metrics) != count * line_height * SCALE:
        raise ValueError("Output SFT validation failed")
    return bytes(result)


def stage() -> None:
    build = json.loads((PROBE / "build.json").read_text(encoding="utf-8"))
    package = Path(build["source_package"])
    manifest_raw = (package / "manifest.json").read_bytes()
    if sha(manifest_raw) != build["source_package_manifest_sha256"]:
        raise ValueError("Immutable source manifest changed")
    manifest = json.loads(manifest_raw)
    destination = PROBE / "runtime/Sprites"
    backup = PROBE / "before-fonts/Sprites"
    if (PROBE / "font-build.json").exists() or backup.exists():
        raise ValueError("Font probe already staged")
    outputs = {}
    for name in NAMES:
        relative = f"Sprites/{name}"
        source = (package / "runtime" / relative).read_bytes()
        current = (destination / name).read_bytes()
        if sha(source) != manifest["files"][relative] or current != source:
            raise ValueError(f"Unknown source font {name}")
        output = scale_sft(source)
        outputs[name] = (source, output)
    backup.mkdir(parents=True)
    report = {"scale": SCALE, "encoding": "coverage-0-63", "source_package_manifest_sha256": sha(manifest_raw), "fonts": {}}
    for name, (source, output) in outputs.items():
        (backup / name).write_bytes(source)
        (destination / name).write_bytes(output)
        report["fonts"][name] = {"before_sha256": sha(source), "after_sha256": sha(output),
                                  "before_bytes": len(source), "after_bytes": len(output)}
    (PROBE / "font-build.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def refine() -> None:
    """Replace the first palette interpretation with verified coverage data."""
    report_path = PROBE / "font-build.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("encoding") == "coverage-0-63":
        raise ValueError("Coverage fonts already staged")
    backup = PROBE / "before-font-coverage/Sprites"
    if backup.exists():
        raise ValueError("Coverage revision backup already exists")
    outputs = {}
    for name, record in report["fonts"].items():
        current = (PROBE / "runtime/Sprites" / name).read_bytes()
        original = (PROBE / "before-fonts/Sprites" / name).read_bytes()
        if sha(current) != record["after_sha256"] or sha(original) != record["before_sha256"]:
            raise ValueError(f"Unexpected font revision: {name}")
        outputs[name] = current, scale_sft(original)
    backup.mkdir(parents=True)
    for name, (current, output) in outputs.items():
        (backup / name).write_bytes(current)
        (PROBE / "runtime/Sprites" / name).write_bytes(output)
        record = report["fonts"][name]
        record["superseded_palette_sha256"] = record["after_sha256"]
        record["after_sha256"] = sha(output)
        record["after_bytes"] = len(output)
    report["encoding"] = "coverage-0-63"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    verify()


def verify() -> None:
    report = json.loads((PROBE / "font-build.json").read_text(encoding="utf-8"))
    for name, record in report["fonts"].items():
        path = PROBE / "runtime/Sprites" / name
        raw = path.read_bytes()
        if sha(raw) != record["after_sha256"]:
            raise ValueError(f"Font probe changed: {name}")
        read_sft(raw)
        if sha((PROBE / "before-fonts/Sprites" / name).read_bytes()) != record["before_sha256"]:
            raise ValueError(f"Font backup changed: {name}")
    print(json.dumps({"verified": len(report["fonts"]), "scale": report["scale"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("stage", "refine", "verify"))
    args = parser.parse_args()
    {"stage": stage, "refine": refine, "verify": verify}[args.command]()
