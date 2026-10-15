"""Baseline-first check that stale page pixels cannot disable battle scaling."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

from PIL import Image

from compare_hd_baseline import CaptureSession, ROOT, sha

OLD = "93b45aa6d8d776a7c02f8c5489d3ff807320d4c690a3b302bc03602a4fbfb2ff"
NEW = "e7d7543505d1044ffd1e15b94a1427b8c3b381413dd4401a5cc4af52fec91ee5"
LAUNCHER_OLD = "0bb54b014be6c2852a346342b10d49778d94a2a9dbb4fdcf9a011dafc5a14ab1"
LAUNCHER_NEW = "d6a4f14134ead911ebeb16e2bfaddfa716e30a677cbe6297af66f9c236f9dfd0"


def main() -> None:
    lab = ROOT / "modernization/playtests/mixed-ui-v4"
    wrapper = lab / "game-wide169/ddraw.dll"
    launcher = lab / "game/Chaos-Mixed-UI-Preview.exe"
    manifest = lab / "manifest.json"
    candidate = ROOT / "modernization/build/cnc-ddraw-src/bin/Release/ddraw.dll"
    candidate_launcher = ROOT / "modernization/build/mixed-ui-v4-runtime/Chaos-Mixed-UI-Preview.exe"
    if sha(wrapper) != OLD or sha(candidate) != NEW or sha(launcher) != LAUNCHER_OLD or sha(candidate_launcher) != LAUNCHER_NEW:
        raise RuntimeError("Wrapper identity changed")
    original_wrapper, original_manifest = wrapper.read_bytes(), manifest.read_bytes()
    original_launcher = launcher.read_bytes()
    m = json.loads(original_manifest)
    if m["files"]["game-wide169/ddraw.dll"] != OLD:
        raise RuntimeError("Manifest identity changed")
    out = ROOT / "modernization/assets/hd/stale-page-fix" / str(time.time_ns())
    out.mkdir(parents=True)
    result = {"baseline": {}, "candidate": {}, "wrapper_sha256": NEW}
    if "--candidate-only" not in sys.argv:
        # Capture the hash-verified installed baseline before replacing any file.
        baseline_dir = out / "baseline-first"
        baseline_dir.mkdir()
        with CaptureSession("baseline", baseline_dir, "mixed-ui-v4") as s:
            time.sleep(12)
            s.shot("menu")
            s.load_fixture("test4", False)
            s.shot("test4-battle")
            result["baseline"] = {"restored": None, "records": s.records, "fixture_sha256": s.result.get("fixture_sha256")}
        result["baseline"]["restored"] = s.result["restored"]
    try:
        wrapper.write_bytes(candidate.read_bytes())
        launcher.write_bytes(candidate_launcher.read_bytes())
        m["files"]["game-wide169/ddraw.dll"] = NEW
        m["files"]["game/Chaos-Mixed-UI-Preview.exe"] = LAUNCHER_NEW
        manifest.write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
        for fixture_name in ("test4", "test3", "test", "test2-legacy", "test7-legacy"):
            run = out / fixture_name
            run.mkdir()
            with CaptureSession("hd", run, "mixed-ui-v4", launcher_sets_mixed=True) as s:
                s.shot("menu")
                s.load_fixture(fixture_name, False)
                s.shot("battle")
                s.key(0x1B)
                time.sleep(.4)
                s.shot("escape")
                battle = s.records["battle"]
                font_ok = battle["font_heights"] == [32, 22, 15]
                esc_ok = [460, 276, 820, 324] in [c["rect"] for c in s.controls()]
                with Image.open(battle["native"]) as im:
                    rgb = im.convert("RGB")
                    roi = rgb.crop((1500, 200, 2300, 1100))
                    lit = sum(max(p) > 8 for p in roi.get_flattened_data()) / (roi.width * roi.height)
                if lit < .10 or not font_ok or not esc_ok:
                    raise RuntimeError(f"Battle validation failed in {fixture_name}: lit={lit:.3f}, font={font_ok}, Esc={esc_ok}")
                result["candidate"][fixture_name] = {"lit_fraction": lit,
                                                      "font_ok": font_ok, "esc_ok": esc_ok,
                                                      "records": s.records,
                                                      "fixture_sha256": s.result.get("fixture_sha256")}
                print(fixture_name, "lit", round(lit, 3), flush=True)
            result["candidate"][fixture_name]["restored"] = s.result["restored"]
        (out / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(out, flush=True)
    finally:
        wrapper.write_bytes(original_wrapper)
        launcher.write_bytes(original_launcher)
        manifest.write_bytes(original_manifest)
        if sha(wrapper) != OLD or sha(launcher) != LAUNCHER_OLD or manifest.read_bytes() != original_manifest:
            raise RuntimeError("Rollback failed")


if __name__ == "__main__":
    main()
