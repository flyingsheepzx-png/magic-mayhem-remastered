"""Compare two Qwen UI assets in a disposable copy of the latest wide169 package.

The copy remains launchable as an opt-in preview. Installed game files are never
modified. The package, original art and generated PNGs are hash checked first.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import time

from PIL import Image, ImageChops, ImageStat

import wide169_trial
from wide169_build import ROOT
from wide169_install import inventory


WORK = ROOT / "modernization/assets/hd"
PREVIEW = WORK / "preview-wide169-v7-qwen"
PACK = WORK / "pack"
QUEUE = WORK / "hd-queue.json"
REPORT = WORK / "wide169-art-trial.json"
ASSETS = (
    "Interface/LoadGame/800x600/Load Game 800-600.JPG",
    "Interface/Grimoire/800x600/Backdrop.JPG",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def candidate(relative: str, record: dict) -> bytes:
    png = PACK / Path(record["output"])
    meta = json.loads(png.with_suffix(png.suffix + ".json").read_text(encoding="utf-8"))
    if record["status"] != "done" or sha(png.read_bytes()) != record["output_sha256"]:
        raise RuntimeError("Unverified Qwen image: " + relative)
    if meta["output_sha256"] != record["output_sha256"] or meta["source_sha256"] != record["source_sha256"]:
        raise RuntimeError("Qwen manifest mismatch: " + relative)
    with Image.open(png) as image:
        if image.format != "PNG" or image.size != (1920, 1440):
            raise RuntimeError("Wrong Qwen image size: " + relative)
        content = image.convert("RGB").resize((960, 720), Image.Resampling.LANCZOS)
    framed = Image.new("RGB", (1280, 720))
    framed.paste(content, (160, 0))
    output = io.BytesIO()
    framed.save(output, "JPEG", quality=100, subsampling=0)
    return output.getvalue()


def capture(phase: str) -> dict:
    wide169_trial.GAME = PREVIEW / "game"
    wide169_trial.LAB = PREVIEW / "game-wide169"
    os.environ["MM_ALLOW_NATIVE_CLIENT"] = "1"
    os.environ["MM_ALLOW_SCALED_CLIENT"] = "1"
    reports = []
    with wide169_trial.Session() as s:
        s.click(640, 456)
        time.sleep(1)
        s.capture("load")
        s.bars("load")
        reports.append(s.run)
    with wide169_trial.Session() as s:
        s.click(640, 396)
        time.sleep(1)
        s.click(976, 66)
        time.sleep(1)
        s.capture("grimoire")
        s.bars("grimoire")
        reports.append(s.run)
    results = [json.loads((path / "result.json").read_text(encoding="utf-8")) for path in reports]
    if any(r["status"] != "completed" for r in results):
        raise RuntimeError("Game capture failed: " + phase)
    return {"load": str(reports[0] / "load.png"), "grimoire": str(reports[1] / "grimoire.png"),
            "runs": [str(path) for path in reports], "checks": [r["checks"] for r in results]}


def image_difference(first: str, second: str) -> dict:
    with Image.open(first) as source, Image.open(second) as target:
        a, b = source.convert("RGB"), target.convert("RGB")
        if a.size != (1280, 720) or b.size != a.size:
            raise RuntimeError("Unexpected game capture size")
        left = a.crop((0, 0, 160, 720))
        right = b.crop((0, 0, 160, 720))
        if ImageChops.difference(left, right).getbbox():
            raise RuntimeError("Left letterbox changed")
        left = a.crop((1120, 0, 1280, 720))
        right = b.crop((1120, 0, 1280, 720))
        if ImageChops.difference(left, right).getbbox():
            raise RuntimeError("Right letterbox changed")
        difference = ImageChops.difference(a.crop((160, 0, 1120, 720)), b.crop((160, 0, 1120, 720)))
        mean = sum(ImageStat.Stat(difference).mean) / 3
        changed = sum(1 for pixel in difference.get_flattened_data() if max(pixel) > 6)
        return {"mean_absolute_rgb": round(mean, 3), "changed_fraction_gt6": round(changed / (960 * 720), 4)}


def recapture() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    package = Path(report["package"])
    preview_runtime = PREVIEW / "game-wide169"
    for relative in ASSETS:
        target = preview_runtime / relative
        if sha(target.read_bytes()) != report["qwen_asset_sha256"][relative]:
            raise RuntimeError("Preview asset changed outside trial: " + relative)
        original = (package / "runtime" / relative).read_bytes()
        if sha(original) != report["original_asset_sha256"][relative]:
            raise RuntimeError("Package original changed: " + relative)
        target.write_bytes(original)
    report["baseline"] = capture("baseline-recheck")
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    records = {row["source"]: row for row in queue["records"]}
    for relative in ASSETS:
        data = candidate(relative, records[relative])
        if sha(data) != report["qwen_asset_sha256"][relative]:
            raise RuntimeError("Candidate changed: " + relative)
        (preview_runtime / relative).write_bytes(data)
    report["candidate"] = capture("candidate-recheck")
    report["comparison"] = {name: image_difference(report["baseline"][name], report["candidate"][name])
                            for name in ("load", "grimoire")}
    if report["comparison"]["grimoire"]["changed_fraction_gt6"] < 0.01:
        raise RuntimeError("Grimoire asset still not visible in game")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "comparison": report["comparison"], "report": str(REPORT)}, indent=2))


def restore_preview() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    package = Path(report["package"])
    for relative in ASSETS:
        target = PREVIEW / "game-wide169" / relative
        if sha(target.read_bytes()) not in (report["qwen_asset_sha256"][relative],
                                            report["original_asset_sha256"][relative]):
            raise RuntimeError("Preview asset changed outside trial: " + relative)
        original = (package / "runtime" / relative).read_bytes()
        if sha(original) != report["original_asset_sha256"][relative]:
            raise RuntimeError("Package original changed: " + relative)
        target.write_bytes(original)
    print("Restored both preview images from the verified v7 package")


def verify_gameplay() -> None:
    wide169_trial.GAME = PREVIEW / "game"
    wide169_trial.LAB = PREVIEW / "game-wide169"
    os.environ["MM_ALLOW_NATIVE_CLIENT"] = "1"
    os.environ["MM_ALLOW_SCALED_CLIENT"] = "1"
    with wide169_trial.Session() as session:
        session.load("test2")
        if session.result["checks"]["surface"] != [1280, 720]:
            raise RuntimeError("Wrong battle surface")
        table = session.i(0x6def58)
        position = [session.i(table + offset) for offset in (8, 12, 16)]
        if position != [66, 48, 6] or session.i(0x6def5c) != 125:
            raise RuntimeError("Wrong test2 battle fixture")
        if session.result["images"]["test2"]["bar_nonblack_fraction"] < 0.1:
            raise RuntimeError("Battle did not render across widened viewport")
        print("Loaded test2 in preview:", session.run)


def main() -> None:
    if "--recapture" in sys.argv:
        recapture()
        return
    if "--restore" in sys.argv:
        restore_preview()
        return
    if "--verify" in sys.argv:
        verify_gameplay()
        return
    if PREVIEW.exists():
        raise RuntimeError("Preview already exists; preserve it and choose a new trial path")
    baseline = json.loads((ROOT / "modernization/current-baseline.json").read_text(encoding="utf-8"))["latest_development"]
    for relative, expected in baseline["files"].items():
        if sha((ROOT / relative).read_bytes()) != expected:
            raise RuntimeError("Latest development identity changed: " + relative)
    state = json.loads((ROOT / "modernization/wide169-installed.json").read_text(encoding="utf-8"))
    package = Path(state["package"])
    manifest_data = (package / "manifest.json").read_bytes()
    if sha(manifest_data) != state["manifest_sha256"]:
        raise RuntimeError("Installed package manifest mismatch")
    manifest = json.loads(manifest_data)
    if inventory(package / "runtime") != manifest["files"]:
        raise RuntimeError("Installed package files changed")
    launcher = package / "Chaos-Wide169-Trial.exe"
    if sha(launcher.read_bytes()) != manifest["launcher_sha256"]:
        raise RuntimeError("Installed package launcher changed")
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    records = {row["source"]: row for row in queue["records"]}
    generated = {}
    for relative in ASSETS:
        row = records[relative]
        source = Path(queue["assets_root"]) / relative
        if sha(source.read_bytes()) != row["source_sha256"]:
            raise RuntimeError("Original source changed: " + relative)
        generated[relative] = candidate(relative, row)
    (PREVIEW / "game").mkdir(parents=True)
    shutil.copytree(package / "runtime", PREVIEW / "game-wide169")
    shutil.copy2(launcher, PREVIEW / "game" / launcher.name)
    (PREVIEW / "game-wide169" / "ss").mkdir(exist_ok=True)
    original = {}
    for relative in ASSETS:
        original[relative] = sha((PREVIEW / "game-wide169" / relative).read_bytes())
        if original[relative] != manifest["files"][relative]:
            raise RuntimeError("Copied original asset mismatch: " + relative)
    report = {"package": str(package), "manifest_sha256": sha(manifest_data),
              "preview_launcher": str(PREVIEW / "game" / launcher.name),
              "original_asset_sha256": original,
              "qwen_asset_sha256": {rel: sha(data) for rel, data in generated.items()}}
    report["baseline"] = capture("baseline")
    for relative, data in generated.items():
        (PREVIEW / "game-wide169" / relative).write_bytes(data)
    report["candidate"] = capture("candidate")
    report["comparison"] = {name: image_difference(report["baseline"][name], report["candidate"][name])
                            for name in ("load", "grimoire")}
    report["status"] = "passed"
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "preview": report["preview_launcher"],
                      "comparison": report["comparison"], "report": str(REPORT)}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        raise
