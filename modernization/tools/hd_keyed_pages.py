"""Derive lossless, dual-key-clean Grimoire pages from verified Qwen outputs.

The producer PNGs and queue are immutable. Each derivative records both source
hashes and its own hash, so it can be staged as a BMP without using JPEG.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from hd_ui_fit import BACKUP, ROOT, STATE, PACK, gate
from qwen_canvas import apply_grimoire_key_template, grimoire_key_template

OUT = ROOT / "modernization/assets/hd/keyed-pages"
SNAPSHOT = ROOT / "modernization/assets/hd/ui-verified-snapshot.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(limit: int = 0) -> dict:
    gate()
    fit = json.loads(STATE.read_text(encoding="utf-8"))
    indices = {row["path"].lower(): (index, row) for index, row in enumerate(fit["files"])}
    records = [row for row in json.loads(SNAPSHOT.read_text(encoding="utf-8"))["records"]
               if row["source"].startswith("Interface/Grimoire/800x600/")
               and row["target_size"] == [960, 1440]]
    if limit:
        records = records[:limit]
    manifest_rows = []
    for row in records:
        index, fitted = indices[row["source"].lower()]
        source_bytes = (BACKUP / str(index)).read_bytes()
        if hashlib.sha256(source_bytes).hexdigest() != row["source_sha256"]:
            raise RuntimeError("Original page hash mismatch: " + row["source"])
        png = PACK / row["output"]
        source_manifest = json.loads(png.with_suffix(png.suffix + ".json").read_text(encoding="utf-8"))
        if digest(png) != row["output_sha256"] or source_manifest["output_sha256"] != row["output_sha256"]:
            raise RuntimeError("Qwen page hash mismatch: " + row["source"])
        with Image.open(BACKUP / str(index)) as handle:
            source = handle.convert("RGB")
        template = grimoire_key_template(source)
        template_path = OUT / "templates" / Path(row["source"]).with_suffix(".png")
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template.save(template_path, format="PNG")
        with Image.open(png) as handle:
            if handle.format != "PNG" or handle.size != (960, 1440):
                raise RuntimeError("Qwen page format or size mismatch")
            cleaned = apply_grimoire_key_template(handle.convert("RGB"), template)
        if ImageChops.difference(cleaned, apply_grimoire_key_template(cleaned, template)).getbbox():
            raise RuntimeError("Key cleanup not idempotent")
        relative = Path(row["source"]).with_suffix(".png")
        target = OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        cleaned.save(target, format="PNG")
        manifest_rows.append({"source": row["source"], "source_sha256": row["source_sha256"],
                              "qwen_png_sha256": row["output_sha256"],
                              "output": str(target.relative_to(OUT)).replace("\\", "/"),
                              "output_sha256": digest(target),
                              "template": str(template_path.relative_to(OUT)).replace("\\", "/"),
                              "template_sha256": digest(template_path),
                              "key_edge_policy": "grimoire-source-template-v2",
                              "manager_job_id": source_manifest["manager_job_id"]})
    report = {"status": "staged-not-installed", "count": len(manifest_rows),
              "records": manifest_rows}
    (OUT / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {"staged": len(manifest_rows), "manifest": str(OUT / "manifest.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="zero stages all completed Grimoire pages")
    args = parser.parse_args()
    print(json.dumps(build(args.limit), indent=2))
