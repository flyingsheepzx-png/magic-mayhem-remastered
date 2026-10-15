"""Read-only SPR v4 frame inventory and PNG export for installed community assets.

Never writes back to SPR/ANI. Unknown layouts fail rather than guessing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image, ImageDraw


def read_spr(path: Path):
    """Parse an SPR v4 container.

    The header is length, version, frame count, palette count and pixel format.
    The 157 originally supported files all happen to have palette count equal to
    pixel format, which made the two look like one duplicated flag. Realm
    terrain uses four palettes over the same 8-bit pixel format, so the fields
    are read separately here: palette count N means N blocks of 768 bytes, and
    pixel format 1 means palette indices while 0 means RGB565.

    Returns (palettes, frames) where palettes is a list of raw palette blocks and
    each frame carries the palette index it selects.
    """
    data = path.read_bytes()
    if len(data) < 24 or data[:4] != b"SPR\0":
        raise ValueError("not SPR")
    length, version, count, palette_count, pixel_format = struct.unpack_from("<5I", data, 4)
    if length != len(data) or version != 4:
        raise ValueError("unsupported header")
    if palette_count > 8 or pixel_format not in (0, 1):
        raise ValueError("unsupported header")
    if pixel_format == 1 and palette_count == 0:
        raise ValueError("palette pixels without a palette")
    table = 24 + 768 * palette_count
    base = table + count * 4
    if not count or base > length:
        raise ValueError("invalid frame table")
    palettes = [data[24 + 768 * i:24 + 768 * (i + 1)] for i in range(palette_count)]
    frames = []
    offsets = list(struct.unpack_from(f"<{count}I", data, table))
    if offsets[0] != 0 or offsets != sorted(set(offsets)):
        raise ValueError("invalid offsets")
    for index, rel in enumerate(offsets):
        start = base + rel
        end = base + offsets[index + 1] if index + 1 < count else length
        frame = data[start:end]
        if len(frame) < 40:
            raise ValueError("truncated frame")
        size, width, height, x, y = struct.unpack_from("<3I2i", frame)
        # Some files have trailing bytes after the final frame. Respect the
        # frame's own length, and record only its bounded payload.
        if size > len(frame) or size < 40 or width > 8192 or height > 8192 or 40 + height * 8 > size:
            raise ValueError(f"invalid frame {index}")
        frame = frame[:size]
        if (width == 0) != (height == 0):
            raise ValueError("only one empty dimension")
        # Each row has alternating transparent skips and opaque runs; pointers
        # are relative to the frame start. Pixels are palette bytes or RGB565.
        spans = []
        for row in range(height):
            run_offset, pixel_offset = struct.unpack_from("<2I", frame, 40 + row * 8)
            if run_offset < 40 + height * 8 or pixel_offset < 40 + height * 8:
                raise ValueError(f"row points into header: {index}/{row}")
            position, cursor, opaque, paint = 0, run_offset, 0, False
            row_spans = []
            while position < width:
                if cursor >= size:
                    raise ValueError("truncated runs")
                run = frame[cursor]
                cursor += 1
                if position + run > width:
                    raise ValueError(f"run exceeds width: {index}/{row}")
                if paint and run:
                    row_spans.append((position, run, pixel_offset + opaque * (1 if pixel_format == 1 else 2)))
                    opaque += run
                position += run
                paint = not paint
                if cursor - run_offset > size:
                    raise ValueError("unterminated runs")
            if pixel_offset + opaque * (1 if pixel_format == 1 else 2) > size:
                raise ValueError("truncated pixels")
            spans.append(row_spans)
        # Legacy inventory calls these "flags". Native 0x57D310 instead uses
        # +28 as palette selector (-1 for RGB565), while +32/+36 are optional
        # mask offsets. Preserve the legacy tuple for existing queue manifests;
        # encoders must not copy those offsets into a resized payload.
        flags = struct.unpack_from("<3I", frame, 28)
        frames.append({"index": index, "width": width, "height": height,
                       "offset": [x, y], "name": frame[20:28].rstrip(b"\0").decode("ascii", "replace"),
                       "flags": flags,
                       # The variant field tracks the palette block count, but using it as
                       # a per-frame selector mixes colour schemes inside one map (a green grass
                       # tile next to a red warrior), so palette 0 is the consistent look.
                       "palette": 0, "variant": flags[0],
                       "data": frame, "spans": spans})
    return palettes, frames


def decode(palettes, frame):
    """Render one frame to RGBA. palettes is the list returned by read_spr."""
    if isinstance(palettes, (bytes, bytearray)):
        palettes = [palettes]
    palette = palettes[frame.get("palette", 0)] if palettes else None
    im = Image.new("RGBA", (frame["width"], frame["height"]))
    pixels = im.load()
    data = frame["data"]
    for y, spans in enumerate(frame["spans"]):
        for x, length, offset in spans:
            for i in range(length):
                if palette is not None:
                    p = data[offset + i] * 3
                    color = tuple(palette[p:p + 3])
                else:
                    p = struct.unpack_from("<H", data, offset + 2 * i)[0]
                    color = ((p >> 11) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31)
                pixels[x + i, y] = (*color, 255)
    return im


def inventory(root, output):
    records = []
    for folder in ("Bitmaps", "Interface", "Realms", "Sprites", "Creatures"):
        for path in sorted((root / folder).rglob("*")):
            if path.suffix.lower() != ".spr":
                continue
            record = {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            try:
                palette, frames = read_spr(path)
                record.update(format="SPR-v4", pixel_format="palette-RGB" if palette else "RGB565",
                              frame_count=len(frames), frames=[{k: f[k] for k in ("index", "name", "width", "height", "offset", "flags")} for f in frames])
            except (ValueError, struct.error) as exc:
                record["error"] = str(exc)
            records.append(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"sprites": records}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(records), "frames": sum(r.get("frame_count", 0) for r in records),
                      "errors": [{"path": r["path"], "error": r["error"]} for r in records if "error" in r]}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=(Path(__file__).resolve().parents[2] / "game"))
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--limit", type=int, default=0, help="0 exports all frames")
    args = parser.parse_args()
    if args.inventory:
        inventory(args.root.resolve(), args.inventory)
        return
    if not args.source or not args.output_dir:
        parser.error("provide --inventory or --source and --output-dir")
    if args.output_dir.exists():
        parser.error("output directory must be new")
    palette, frames = read_spr(args.source)
    args.output_dir.mkdir(parents=True)
    selected = frames[:args.limit] if args.limit > 0 else frames
    cols, cell = 8, 180
    sheet = Image.new("RGB", (cols * cell, ((len(selected) + cols - 1) // cols) * cell), "#282828")
    draw = ImageDraw.Draw(sheet)
    records = []
    for f in selected:
        if not f["width"] or not f["height"]:
            records.append({k: f[k] for k in ("index", "name", "width", "height", "offset", "flags")})
            continue
        im = decode(palette, f)
        name = f"{f['index']:04d}.png"
        im.save(args.output_dir / name)
        # Nearest-neighbor preview exposes original pixels without inventing detail.
        preview = im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST)
        preview.thumbnail((cell - 10, cell - 30), Image.Resampling.NEAREST)
        x, y = (f["index"] % cols) * cell, (f["index"] // cols) * cell
        sheet.paste(preview, (x + (cell - preview.width) // 2, y + 25), preview)
        draw.text((x + 5, y + 5), f"{f['index']} {f['name']} {im.width}x{im.height}", fill="white")
        record = {k: f[k] for k in ("index", "name", "width", "height", "offset", "flags")}
        record.update(file=name, sha256=hashlib.sha256((args.output_dir / name).read_bytes()).hexdigest())
        records.append(record)
    sheet.save(args.output_dir / "contact-sheet.png")
    (args.output_dir / "manifest.json").write_text(json.dumps({"source": str(args.source.resolve()),
        "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
        "status": "decoded-experimental-not-installed", "ani_mapping": "not decoded", "frames": records}, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(selected)}/{len(frames)} frames to {args.output_dir}")


if __name__ == "__main__":
    main()
