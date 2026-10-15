"""Verify completed Qwen UI outputs, then copy them into the isolated HD lab.

This reads the producer queue. It never starts, stops or alters that batch.
The copied queue snapshot permits later fits without reading the source game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from hd_menu_fit import ROOT, SUPPORTED_EXE
from hd_verify import verify


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync(source_root: Path) -> dict:
    source_root = source_root.resolve(strict=True)
    marker = json.loads((ROOT / "modernization/assets/hd/HD_LAB.json").read_text(encoding="utf-8-sig"))
    if marker.get("kind") != "isolated-hd-game-lab" or Path(marker["root"]).resolve() != ROOT:
        raise RuntimeError("Refusing outside isolated HD lab")
    if digest(ROOT / "Chaos.exe") != SUPPORTED_EXE:
        raise RuntimeError("Unknown community executable")
    queue_path = source_root / "modernization/assets/hd/hd-queue.json"
    pack = source_root / "modernization/assets/hd/pack"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    if Path(queue["assets_root"]).resolve() != source_root:
        raise RuntimeError("Queue source root does not match")
    records = [row for row in queue["records"] if row.get("status") == "done"
               and row.get("route") == "composite" and row.get("category", "").startswith("ui-")]
    failures = [(row["source"], error) for row in records
                if (error := verify(row, source_root, pack))]
    if failures:
        raise RuntimeError(f"Completed UI verification failed: {failures[:8]}")
    target_pack = ROOT / "modernization/assets/hd/pack"
    for row in records:
        source = pack / row["output"]
        target = target_pack / row["output"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or digest(target) != row["output_sha256"]:
            shutil.copy2(source, target)
        manifest = source.with_suffix(source.suffix + ".json")
        shutil.copy2(manifest, target.with_suffix(target.suffix + ".json"))
    report = {"source_queue_sha256": digest(queue_path), "source_root": str(source_root),
              "records": records}
    snapshot = ROOT / "modernization/assets/hd/ui-verified-snapshot.json"
    snapshot.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {"verified_and_copied": len(records), "snapshot": str(snapshot)}


if __name__ == "__main__":
    if (Path(__file__).resolve().parents[2]/'modernization/assets/hd/seedvr2-ui-1.1/plan.json').exists():
        raise RuntimeError('Prior generation/review retired by user; use seedvr_ui_11.py and the SeedVR2 production root')

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    result = sync(parser.parse_args().source_root)
    print(json.dumps(result, indent=2))
