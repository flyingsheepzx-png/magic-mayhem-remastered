"""Verify prepared HD raster outputs without touching installed game files."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qwen_canvas  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(record: dict, root: Path, pack: Path) -> str | None:
    source = root / record["source"]
    output = pack / record["output"]
    manifest_path = output.with_suffix(output.suffix + ".json")
    if not source.is_file() or not output.is_file() or not manifest_path.is_file():
        return "missing source, output or manifest"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256(source) != record["source_sha256"] or manifest.get("source_sha256") != record["source_sha256"]:
        return "source hash mismatch"
    output_hash = sha256(output)
    if output_hash != record.get("output_sha256") or output_hash != manifest.get("output_sha256"):
        return "output hash mismatch"
    if not manifest.get("manager_job_id"):
        return "missing Manager job ID"
    with Image.open(source) as handle:
        source_rgba = handle.convert("RGBA")
    with Image.open(output) as handle:
        if handle.format != "PNG" or list(handle.size) != record["target_size"]:
            return "output format or size mismatch"
        result = handle.convert("RGB")
    alpha = source_rgba.getchannel("A")
    if alpha.getextrema()[0] < 255:
        expected = alpha.resize(result.size, Image.Resampling.LANCZOS)
        with Image.open(output) as handle:
            actual = handle.convert("RGBA").getchannel("A")
        if ImageChops.difference(actual, expected).getbbox():
            return "alpha coverage mismatch"
    else:
        source_rgb = source_rgba.convert("RGB")
        grimoire = ("Grimoire" in source.parts and "800x600" in source.parts
                    and source_rgb.size == (400, 600))
        if grimoire and manifest.get("key_edge_policy") in ("grimoire-dual-key-guard-v1", "grimoire-source-template-v2"):
            expected = qwen_canvas.protect_grimoire_keys(result, source_rgb)
            if ImageChops.difference(result, expected).getbbox():
                return "Grimoire dual colour-key or guard mismatch"
        else:
            _key, mask, _fraction = qwen_canvas.detect_key_mask(source_rgb)
            if mask is not None:
                protected = mask.resize(result.size, Image.Resampling.NEAREST).filter(ImageFilter.MaxFilter(5))
                nearest = source_rgb.resize(result.size, Image.Resampling.NEAREST)
                mismatch = ImageChops.difference(result, nearest)
                if ImageChops.multiply(mismatch, protected.convert("RGB")).getbbox():
                    return "colour-key or rim mismatch"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=Path("modernization/assets/hd/hd-queue.json"))
    parser.add_argument("--pack", type=Path, default=Path("modernization/assets/hd/pack"))
    parser.add_argument("--category", action="append")
    args = parser.parse_args()
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    root = Path(queue["assets_root"])
    records = [r for r in queue["records"] if r["route"] == "composite" and r["status"] == "done"
               and (not args.category or r["category"] in args.category)]
    failures = []
    for record in records:
        try:
            error = verify(record, root, args.pack)
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            error = str(exc)
        if error:
            failures.append((record["source"], error))
    for source, error in failures:
        print("FAIL", source, error)
    print("Verified %d completed raster assets; %d failed" % (len(records), len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
