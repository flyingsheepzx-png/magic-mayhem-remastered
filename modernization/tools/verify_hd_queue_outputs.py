"""Verify completed generated asset manifests and every recorded output hash."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "modernization/assets/hd/hd-queue.json"
PACK = ROOT / "modernization/assets/hd/pack"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    totals = {"records": 0, "raster": 0, "containers": 0, "frames": 0}
    failures = []
    for record in queue["records"]:
        if record["status"] != "done":
            continue
        totals["records"] += 1
        output = PACK / record["output"]
        try:
            if record["route"] == "composite":
                totals["raster"] += 1
                if sha(output) != record["output_sha256"]:
                    raise ValueError("raster SHA mismatch")
                metadata = json.loads(output.with_suffix(output.suffix + ".json").read_text(encoding="utf-8"))
                if metadata["source_sha256"] != record["source_sha256"]:
                    raise ValueError("raster source SHA mismatch")
            elif record["route"] in {"sheet", "atlas"}:
                totals["containers"] += 1
                metadata = json.loads((output / "sprite.json").read_text(encoding="utf-8"))
                if not metadata["complete"] or metadata["source_sha256"] != record["source_sha256"]:
                    raise ValueError("sprite manifest incomplete or source mismatch")
                for frame in metadata["frames"]:
                    if sha(output / frame["file"]) != frame["sha256"]:
                        raise ValueError("sprite frame SHA mismatch: " + frame["file"])
                    totals["frames"] += 1
            else:
                raise ValueError("unsupported completed route")
        except (OSError, KeyError, ValueError) as exc:
            failures.append({"source": record["source"], "error": str(exc)})
    result = {**totals, "failures": failures}
    print(json.dumps(result, indent=2))
    if failures:
        raise RuntimeError("HD outputs failed verification")


if __name__ == "__main__":
    main()
