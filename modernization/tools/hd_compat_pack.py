"""Stage same-path 800x600-compatible JPGs from completed HD UI outputs.

This tests generated content through the legacy loader. It deliberately leaves
keyed images and other formats pending; the staged files never touch the game.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qwen_canvas  # noqa: E402


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--out", type=Path,
                        default=Path("modernization/assets/hd/compat-800"))
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    source_root = Path(queue["assets_root"])
    entries = []
    skipped = {}
    selected = [r for r in queue["records"] if r["status"] == "done"
                and r["category"].startswith("ui-") and r["route"] == "composite"]
    if args.limit:
        selected = selected[:args.limit]
    for record in selected:
        source = source_root / record["source"]
        restored = args.pack / record["output"]
        manifest_path = restored.with_suffix(restored.suffix + ".json")
        suffix = source.suffix.lower()
        if suffix not in {".jpg", ".jpeg"}:
            skipped[suffix] = skipped.get(suffix, 0) + 1
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (digest(source) != record["source_sha256"]
                or digest(restored) != record.get("output_sha256")
                or manifest.get("output_sha256") != record.get("output_sha256")):
            raise RuntimeError("Source or HD output hash mismatch: " + record["source"])
        with Image.open(source) as handle:
            source_image = handle.convert("RGB")
        _key, mask, _fraction = qwen_canvas.detect_key_mask(source_image)
        if mask is not None:
            skipped["keyed-jpeg"] = skipped.get("keyed-jpeg", 0) + 1
            continue
        with Image.open(restored) as handle:
            if handle.format != "PNG" or list(handle.size) != record["target_size"]:
                raise RuntimeError("Unexpected HD output format/size: " + record["source"])
            compatible = handle.convert("RGB").resize(source_image.size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        compatible.save(buffer, format="JPEG", quality=100, subsampling=0)
        relative = Path(record["source"])
        target = args.out / "pack" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(buffer.getvalue())
        entries.append({"source": record["source"],
                        "source_sha256": record["source_sha256"],
                        "hd_png_sha256": record["output_sha256"],
                        "compatible_sha256": digest(target),
                        "size": list(source_image.size),
                        "manager_job_id": manifest["manager_job_id"]})
    args.out.mkdir(parents=True, exist_ok=True)
    report = {"status": "staged-not-installed", "purpose": "legacy loader content check",
              "native_2k_ui": False, "entries": entries, "skipped": skipped}
    (args.out / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Staged %d compatible JPGs; skipped %s" % (len(entries), skipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
