"""Test Qwen canvas restoration on a decoded SPR sequence.

Sequence frames are the hard case for generative restoration: every frame has to
keep the same geometry as its neighbours or the animation flickers. This tool
compares two ways of running the canvas pipeline on a sprite:

- per frame: each frame gets its own canvas. Small frames force a very large
  content scale, so the model has almost no subject and invents freely.
- per sheet: every frame goes into one grid image, which is restored once and
  split again. The sheet is much larger than a frame, so the content scale drops
  sharply, and the model sees one consistent material instead of sixteen
  unrelated scraps.

Both routes are measured against the same Lanczos baseline for sharpness and for
frame to frame flicker, and the frames keep the sprite's own placement offsets so
the comparison is in animation space rather than in individual frame space.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qwen_canvas  # noqa: E402
from spr_assets import decode, read_spr  # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def load_frames(path: Path, start: int, count: int) -> list:
    palette, frames = read_spr(path)
    chosen = [f for f in frames[start:start + count] if f["width"] and f["height"]]
    if not chosen:
        raise SystemExit("No non-empty frames in the requested range")
    min_x = min(f["offset"][0] for f in chosen)
    min_y = min(f["offset"][1] for f in chosen)
    max_x = max(f["offset"][0] + f["width"] for f in chosen)
    max_y = max(f["offset"][1] + f["height"] for f in chosen)
    width, height = max_x - min_x, max_y - min_y
    aligned = []
    for frame in chosen:
        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        canvas.paste(decode(palette, frame), (frame["offset"][0] - min_x, frame["offset"][1] - min_y))
        aligned.append((frame, canvas))
    return aligned


def to_rgb(image: Image.Image) -> Image.Image:
    """Flat black behind transparency, so the canvas is a normal photo-like image."""
    background = Image.new("RGB", image.size, (0, 0, 0))
    background.paste(image, (0, 0), image)
    return background


def apply_alpha(rgb: Image.Image, alpha_source: Image.Image) -> Image.Image:
    """Never let the model decide coverage; take it from the original frame."""
    alpha = alpha_source.convert("L").resize(rgb.size, Image.Resampling.LANCZOS)
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def restore_image(rgb: Image.Image, target: tuple, args, tag: str, out_dir: Path) -> tuple:
    scale = target[0] / rgb.size[0]
    preset, row = qwen_canvas.choose_preset(rgb.size, scale)
    canvas, box = qwen_canvas.compose(rgb, preset)
    canvas.save(out_dir / (tag + "_canvas.png"))
    generated, job_id, seconds = qwen_canvas.restore(canvas, "%dx%d" % preset, args.steps,
                                                     args.seed, args.timeout)
    (out_dir / (tag + "_raw.png")).write_bytes(generated)
    with Image.open(Path(out_dir / (tag + "_raw.png"))) as handle:
        restored = handle.convert("RGB")
    if restored.size != preset:
        restored = restored.resize(preset, Image.Resampling.LANCZOS)
    content = restored.crop(box).resize(target, Image.Resampling.LANCZOS)
    info = {"preset": list(preset), "content_scale": row["scale"], "job_id": job_id,
            "seconds": seconds, "canvas": canvas.size, "content_box": list(box)}
    return content, info


def sharpness(image: Image.Image) -> float:
    return ImageStat.Stat(image.convert("L").filter(ImageFilter.FIND_EDGES)).stddev[0]


def flicker(images: list) -> float:
    """Mean absolute frame to frame difference; lower means a steadier animation."""
    grey = [im.convert("L") for im in images]
    deltas = [sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 1.0
              for a, b in zip(grey, grey[1:])]
    return sum(deltas) / len(deltas) if deltas else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--frames", type=int, default=16)
    parser.add_argument("--scale", type=float, default=2.0)
    parser.add_argument("--strength", type=float, default=0.6)
    parser.add_argument("--detail-blur", type=float, default=1.6)
    parser.add_argument("--gap", type=int, default=4)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--seed", type=int, default=260926)
    parser.add_argument("--timeout", type=int, default=2400)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    frames = load_frames(args.source.resolve(strict=True), args.start, args.frames)
    base_size = frames[0][1].size
    target = (round(base_size[0] * args.scale), round(base_size[1] * args.scale))
    print("source %s   %d frames %s   target %s" % (args.source.name, len(frames), base_size, target))

    base_frames = [to_rgb(image).resize(target, Image.Resampling.LANCZOS) for _, image in frames]
    alpha_frames = [image.getchannel("A") for _, image in frames]
    baseline_info = {"sharpness": sharpness(base_frames[0]), "flicker": flicker(base_frames)}

    # --- per frame -------------------------------------------------------
    per_frame = []
    started = time.monotonic()
    for index, rgb in enumerate(base_frames):
        content, info = restore_image(rgb, target, args, "frame%03d" % index, args.out_dir)
        composite = qwen_canvas.detail_composite(rgb, content, args.strength, args.detail_blur)
        per_frame.append(composite)
        if index == 0:
            print("per-frame first job: preset %s scale %.2f %.1fs"
                  % ("%dx%d" % tuple(info["preset"]), info["content_scale"], info["seconds"]))
    per_frame_seconds = round(time.monotonic() - started, 1)

    # --- per sheet -------------------------------------------------------
    count = len(frames)
    cols = max(1, math.ceil(math.sqrt(count)))
    rows = math.ceil(count / cols)
    cell_w, cell_h = target
    gap = args.gap
    sheet_w = cols * cell_w + (cols - 1) * gap
    sheet_h = rows * cell_h + (rows - 1) * gap
    sheet = Image.new("RGB", (sheet_w, sheet_h), (0, 0, 0))
    for index, rgb in enumerate(base_frames):
        x = (index % cols) * (cell_w + gap)
        y = (index // cols) * (cell_h + gap)
        sheet.paste(rgb, (x, y))
    sheet_target = (round(sheet_w * args.scale), round(sheet_h * args.scale))
    sheet.save(args.out_dir / "sheet_base.png")
    started = time.monotonic()
    sheet_content, sheet_info = restore_image(sheet, sheet_target, args, "sheet", args.out_dir)
    sheet_seconds = round(time.monotonic() - started, 1)
    print("sheet job: %dx%d -> preset %s content scale %.2f %.1fs"
          % (sheet.size[0], sheet.size[1], "%dx%d" % tuple(sheet_info["preset"]),
             sheet_info["content_scale"], sheet_info["seconds"]))

    blurred = sheet_content.filter(ImageFilter.GaussianBlur(args.detail_blur))
    sheet_detail = ImageChops.subtract(sheet_content, blurred, offset=128)
    per_sheet = []
    for index, rgb in enumerate(base_frames):
        x = (index % cols) * (cell_w + gap) * 2
        y = (index // cols) * (cell_h + gap) * 2
        detail = sheet_detail.crop((x, y, x + target[0], y + target[1]))
        enhanced = ImageChops.add(rgb, detail, offset=-128)
        weight = qwen_canvas.structure_weight(to_rgb(frames[index][1]), rgb.size).point(
            lambda v: round(v * args.strength))
        per_sheet.append(Image.composite(enhanced, rgb, weight))
    sheet_content.save(args.out_dir / "sheet_qwen.png")

    report = {
        "status": "experimental-unreviewed-not-installed",
        "tool": "spr_sequence.py",
        "source": str(args.source),
        "frames": count,
        "frame_range": [args.start, args.start + count - 1],
        "frame_size": list(base_size),
        "target_size": list(target),
        "scale": args.scale,
        "strength": args.strength,
        "steps": args.steps,
        "seed": args.seed,
        "baseline": baseline_info,
        "per_frame": {"sharpness": sharpness(per_frame[0]), "flicker": flicker(per_frame),
                      "wall_seconds": per_frame_seconds, "jobs": count,
                      "content_scale": None},
        "per_sheet": {"sharpness": sharpness(per_sheet[0]), "flicker": flicker(per_sheet),
                      "wall_seconds": sheet_seconds, "jobs": 1,
                      "content_scale": sheet_info["content_scale"],
                      "grid": [cols, rows], "sheet_size": list(sheet.size),
                      "preset": sheet_info["preset"], "job_id": sheet_info["job_id"]},
    }
    (args.out_dir / "sequence-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print()
    print("%-14s %10s %10s %10s %6s" % ("variant", "sharpness", "flicker", "seconds", "jobs"))
    for key in ("baseline", "per_frame", "per_sheet"):
        entry = report[key]
        print("%-14s %10.3f %10.3f %10.1f %6s" % (
            key, entry["sharpness"], entry["flicker"],
            entry.get("wall_seconds", 0.0), entry.get("jobs", 0)))

    # --- review artefacts ------------------------------------------------
    variants = [("lanczos", base_frames), ("per-frame", per_frame), ("per-sheet", per_sheet)]
    show = min(count, 8)
    tw, th = 200, round(200 * base_size[1] / base_size[0])
    sheet_review = Image.new("RGB", (tw * show + 20, (th + 26) * 3 + 10), "#141414")
    draw = ImageDraw.Draw(sheet_review)
    for row, (label, images) in enumerate(variants):
        draw.text((8, 6 + row * (th + 26)), label, fill="white")
        for column in range(show):
            im = images[column].convert("RGB").resize((tw, th), Image.Resampling.NEAREST)
            sheet_review.paste(im, (10 + column * tw, 22 + row * (th + 26)))
    sheet_review.save(args.out_dir / "sequence-review.png")
    print("review sheet", sheet_review.size)

    for label, images in variants:
        rgba = [apply_alpha(im, alpha) for im, alpha in zip(images, alpha_frames)]
        rgba[0].save(args.out_dir / ("anim-%s.gif" % label), save_all=True,
                     append_images=rgba[1:], duration=120, loop=0, disposal=2)
    print("gifs written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
