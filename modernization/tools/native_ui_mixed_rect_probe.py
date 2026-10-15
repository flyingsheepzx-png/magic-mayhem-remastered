"""Reversible scene-rectangle-only experiment in the ignored UI probe."""
from __future__ import annotations

import json
import shutil
import struct
import sys
import pefile

from native_ui_2k_probe import OUT, LAB, ENGINE, digest

WIDTH_VA = 0x5E1728
HEIGHT_VA = 0x5E172C
VALUES = ((WIDTH_VA, 2560, 1280), (HEIGHT_VA, 1440, 720))


def verify_latest():
    root = OUT.parents[3]
    baseline = json.loads((root / "modernization/current-baseline.json").read_text(encoding="utf-8"))
    latest = baseline["latest_development"]
    manifest = root / latest["installed_manifest"]
    if latest["entry"] != "game/Chaos-Wide169-Trial.exe" or not manifest.is_file():
        raise RuntimeError("Latest development entry or installed manifest changed")
    installed = json.loads(manifest.read_text(encoding="utf-8"))
    if installed["status"] != "installed":
        raise RuntimeError("Installed manifest invalid")
    source_engine = root / latest["engine"]
    if digest(source_engine.read_bytes()) != latest["files"][latest["engine"]]:
        raise RuntimeError("Latest installed engine differs from baseline")


def activate():
    verify_latest()
    manifest_path = OUT / "build.json"
    build = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = ENGINE.read_bytes()
    installed = json.loads((OUT.parents[3] / "modernization/wide169-installed.json").read_text(encoding="utf-8"))
    if build["source_package_manifest_sha256"] != installed["manifest_sha256"]:
        raise RuntimeError("Probe source package differs from installed baseline")
    if "mixed_rect" in build or digest(source) != "9ee77fc85a0aa5ab1f5ded984ad8c07e540ca8f33e3f43e92580ab6b082b017d":
        raise RuntimeError("Unknown current probe engine")
    backup = OUT / "before-mixed-rect"
    saved = (backup / ENGINE.name).read_bytes()
    saved_build = json.loads((backup / "build.json").read_text(encoding="utf-8"))
    if digest(saved) != digest(source) or saved_build["patched_engine_sha256"] != digest(source):
        raise RuntimeError("Mixed-rect rollback backup differs")
    pe = pefile.PE(data=source)
    out = bytearray(source)
    for va, before, after in VALUES:
        off = pe.get_offset_from_rva(va - 0x400000)
        if source[off:off + 4] != struct.pack("<I", before):
            raise RuntimeError("Unexpected rect bytes at " + hex(va))
        out[off:off + 4] = struct.pack("<I", after)
    if digest(out) != "531ca844330ed03c4314e762a4f23f4b72db9ca30ec88608023103099ab80ac0":
        raise RuntimeError("Reactivated engine differs from prior experiment")
    ENGINE.write_bytes(out)
    build["mixed_rect"] = {"before_sha256": digest(source), "after_sha256": digest(out),
                           "changes": [{"va": hex(va), "before": before, "after": after}
                                       for va, before, after in VALUES], "status": "diagnostic-not-accepted"}
    build["patched_engine_sha256"] = digest(out)
    manifest_path.write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(build["mixed_rect"], indent=2))


def stage():
    manifest_path = OUT / "build.json"
    build = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = ENGINE.read_bytes()
    if "mixed_rect" in build or digest(source) != build["patched_engine_sha256"]:
        raise RuntimeError("Unrecognized current probe or already staged")
    pe = pefile.PE(data=source)
    out = bytearray(source)
    for va, before, after in VALUES:
        off = pe.get_offset_from_rva(va - 0x400000)
        if source[off:off + 4] != struct.pack("<I", before):
            raise RuntimeError("Unexpected rect bytes at " + hex(va))
        out[off:off + 4] = struct.pack("<I", after)
    backup = OUT / "before-mixed-rect"
    if backup.exists():
        raise RuntimeError("Mixed-rect backup already exists")
    backup.mkdir()
    shutil.copy2(ENGINE, backup / ENGINE.name)
    shutil.copy2(manifest_path, backup / "build.json")
    ENGINE.write_bytes(out)
    build["mixed_rect"] = {"before_sha256": digest(source),
                            "after_sha256": digest(out),
                            "changes": [{"va": hex(va), "before": before, "after": after}
                                        for va, before, after in VALUES],
                            "status": "diagnostic-not-accepted"}
    build["patched_engine_sha256"] = digest(out)
    manifest_path.write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(build["mixed_rect"], indent=2))


def rollback():
    manifest_path = OUT / "build.json"
    build = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = build["mixed_rect"]
    if digest(ENGINE.read_bytes()) != record["after_sha256"]:
        raise RuntimeError("Current mixed rect changed; refusing rollback")
    backup = OUT / "before-mixed-rect"
    old_engine = (backup / ENGINE.name).read_bytes()
    old_manifest = (backup / "build.json").read_bytes()
    if digest(old_engine) != record["before_sha256"] or json.loads(old_manifest)["patched_engine_sha256"] != digest(old_engine):
        raise RuntimeError("Backup identity mismatch")
    ENGINE.write_bytes(old_engine)
    manifest_path.write_bytes(old_manifest)
    print(json.dumps({"rolled_back": True, "engine_sha256": digest(old_engine)}))


if __name__ == "__main__":
    {"stage": stage, "activate": activate, "rollback": rollback}[sys.argv[1]]()
