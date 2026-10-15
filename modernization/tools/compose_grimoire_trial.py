"""Preserve original geometry and add only Qwen-generated page texture detail.

CPU postprocessing, not a separate image generation model. This composition
is specific to the installed 800x600 blank grimoire backdrop.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.resolve() in {args.source.resolve(), args.candidate.resolve()}:
        parser.error("output must be a new file")
    with Image.open(args.source) as source:
        if source.size != (800, 600):
            parser.error("expected installed 800x600 backdrop")
        original = source.convert("RGB").resize((1600, 1200), Image.Resampling.LANCZOS)
    with Image.open(args.candidate) as candidate:
        edited = candidate.convert("RGB").resize(original.size, Image.Resampling.LANCZOS)
    # Exclude spine, outer book boundary, tabs and clasps. The generated detail
    # does not replace low-frequency geometry, luminance or color.
    mask = Image.new("L", original.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon([(120, 76), (764, 76), (764, 1100), (120, 1100)], fill=255)
    draw.polygon([(836, 76), (1450, 76), (1450, 1100), (836, 1100)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(16))
    mask.paste(0, (778, 0, 822, 1200))  # Keep original spine exactly.
    detail = ImageChops.subtract(edited, edited.filter(ImageFilter.GaussianBlur(2.4)), offset=128)
    enhanced = ImageChops.add(original, detail, offset=-128)
    weight = mask.point(lambda value: round(value * 0.65))
    merged = Image.composite(enhanced, original, weight)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    merged.save(args.output)
    manifest = {
        "status": "experimental-reviewed-not-installed",
        "method": "Original geometry/color with 0.65-strength Qwen21 high-frequency detail on page interiors only",
        "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
        "candidate_sha256": hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
        "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "size": [1600, 1200], "generated_texture_model": "Qwen-Image 2.1",
        "geometry": "All low-frequency structure and unmasked borders derive from original",
    }
    args.output.with_suffix(".json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    comparison = Image.new("RGB", (1600, 630), "#202020")
    comparison.paste(original.resize((800, 600), Image.Resampling.LANCZOS), (0, 30))
    comparison.paste(merged.resize((800, 600), Image.Resampling.LANCZOS), (800, 30))
    draw = ImageDraw.Draw(comparison)
    draw.text((12, 8), "Original (reference scaled)", fill="white")
    draw.text((812, 8), "Qwen 2.1 texture detail, original geometry", fill="white")
    comparison.save(args.output.with_name(args.output.stem + "_comparison.png"))
    print(args.output)


if __name__ == "__main__":
    main()
