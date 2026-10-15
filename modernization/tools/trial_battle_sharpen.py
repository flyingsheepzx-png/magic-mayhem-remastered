"""Capture reversible isolated battle sharpen levels with the verified fixture."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time

from compare_hd_baseline import CaptureSession, ROOT, sha


EXPECTED_FIXTURE = "56108a097a01f0bf7a9035d031d96a630e60c43be77808b9c567c65c33cba66d"
EXPECTED_WRAPPER = "015a369ee8b8654434b3e745e61befe63346db521f4bb6acc5b3aca1e9e7796d"
EXPECTED_CANDIDATE = "015a369ee8b8654434b3e745e61befe63346db521f4bb6acc5b3aca1e9e7796d"


def main() -> None:
    lab = ROOT / "modernization/playtests/mixed-ui-v4"
    runtime = lab / "game-wide169"
    wrapper = runtime / "ddraw.dll"
    manifest_path = lab / "manifest.json"
    fixture = runtime / "Save/test2.sav"
    source = ROOT / "modernization/backups/save-recovery/1790661735830701800/test2.sav"
    candidate = ROOT / "modernization/build/cnc-ddraw-src/bin/Release/ddraw.dll"
    if sha(wrapper) != EXPECTED_WRAPPER or sha(source) != EXPECTED_FIXTURE:
        raise RuntimeError("Unexpected isolated wrapper or fixture")
    if fixture.exists():
        raise RuntimeError("Fixture already exists; leave the existing save untouched")
    original_wrapper = wrapper.read_bytes()
    original_manifest = manifest_path.read_bytes()
    report = json.loads(original_manifest)
    if report["files"]["game-wide169/ddraw.dll"] != EXPECTED_WRAPPER:
        raise RuntimeError("Manifest does not describe the current wrapper")
    destination = ROOT / "modernization/assets/hd/battle-sharpen-trial" / str(time.time_ns())
    destination.mkdir(parents=True)
    candidate_bytes = candidate.read_bytes()
    candidate_sha = hashlib.sha256(candidate_bytes).hexdigest()
    if candidate_sha != EXPECTED_CANDIDATE:
        raise RuntimeError("Unexpected optimized wrapper")
    results = {"candidate_sha256": candidate_sha, "original_wrapper_sha256": EXPECTED_WRAPPER}
    try:
        fixture.write_bytes(source.read_bytes())
        wrapper.write_bytes(candidate_bytes)
        report["files"]["game-wide169/ddraw.dll"] = candidate_sha
        manifest_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        for level in ("0", "1", "2"):
            os.environ["MM_PROBE_BATTLE_SHARPEN"] = level
            level_dir = destination / ("level-" + level)
            level_dir.mkdir()
            with CaptureSession("hd", level_dir, "mixed-ui-v4") as session:
                session.shot("menu")
                session.load_fixture("test2", False)
                session.shot("battle")
                session.key(0x1b)
                time.sleep(.4)
                session.shot("escape")
                results[level] = dict(session.records)
        (destination / "trial.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(destination, flush=True)
    finally:
        os.environ.pop("MM_PROBE_BATTLE_SHARPEN", None)
        wrapper.write_bytes(original_wrapper)
        manifest_path.write_bytes(original_manifest)
        if fixture.exists() and sha(fixture) == EXPECTED_FIXTURE:
            fixture.unlink()
        if sha(wrapper) != EXPECTED_WRAPPER or manifest_path.read_bytes() != original_manifest:
            raise RuntimeError("Isolated package restoration failed")


if __name__ == "__main__":
    main()
