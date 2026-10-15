"""Fit legacy full-screen UI layouts and JPG backgrounds in the isolated HD lab.

The native game canvas is 1120x840. First resize the existing assets and layout;
generated replacements are an explicit second step. Rect2 and named 800x600
coordinates follow the same independent x/y scale. Original bytes are retained.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import re

from PIL import Image
import qwen_canvas

from hd_menu_fit import ROOT, SUPPORTED_EXE, apply as apply_old_menu_fit

NATIVE_SIZE = (1120, 840)
LEGACY_SIZE = (800, 600)
STATE = ROOT / "modernization/assets/hd/ui-fit.json"
BACKUP = ROOT / "modernization/assets/hd/backups/ui-fit"
SNAPSHOT = ROOT / "modernization/assets/hd/ui-verified-snapshot.json"
PACK = ROOT / "modernization/assets/hd/pack"
SAMPLE_SELECTION = ROOT / "modernization/assets/hd/ui-samples-enabled.json"
KEYED_STATE = ROOT / "modernization/assets/hd/ui-keyed-bmp.json"
RECT2 = re.compile(rb"(?m)^(\s*Rect2\s*=\s*)(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)")
NAMED = re.compile(rb"(?m)^(\s*800x600_([A-Za-z0-9_]+)\s*=\s*)(-?\d+)")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def gate() -> None:
    marker = json.loads((ROOT / "modernization/assets/hd/HD_LAB.json").read_text(encoding="utf-8-sig"))
    if marker.get("kind") != "isolated-hd-game-lab" or Path(marker["root"]).resolve() != ROOT:
        raise RuntimeError("Refusing outside isolated HD lab")
    if sha((ROOT / "Chaos.exe").read_bytes()) != SUPPORTED_EXE:
        raise RuntimeError("Unknown community executable")


def scale(value: int, axis: int) -> int:
    numerator = NATIVE_SIZE[axis]
    denominator = LEGACY_SIZE[axis]
    return (value * numerator + denominator // 2) // denominator if value >= 0 else -(
        (-value * numerator + denominator // 2) // denominator)


def fit_cfg(data: bytes) -> tuple[bytes, int, int]:
    def rect(match: re.Match[bytes]) -> bytes:
        values = [int(match[i]) for i in range(2, 6)]
        return match[1] + b",".join(str(scale(v, i % 2)).encode() for i, v in enumerate(values))

    data, rect_count = RECT2.subn(rect, data)

    def named(match: re.Match[bytes]) -> bytes:
        name = match[2].lower()
        axis = 1 if name.endswith((b"y", b"top", b"bottom", b"height")) else 0
        return match[1] + str(scale(int(match[3]), axis)).encode()

    data, named_count = NAMED.subn(named, data)
    if b"VAR_LAWCOST" in data and b"[SPRITEBAR_3]" in data:
        # Layout scales 1.4x; the retained 40-pixel talisman sprites need +14
        # to keep their centres aligned with the scaled 50-pixel text rows.
        data = re.sub(rb"(Rect2=378,)(504|574|644)(,0,0)",
                      lambda m: m[1]+str(int(m[2])+14).encode()+m[3], data)
    return data, rect_count, named_count


def target_image_size(relative: Path, source_size: tuple[int, int]) -> tuple[int, int] | None:
    if source_size == LEGACY_SIZE:
        return NATIVE_SIZE
    if relative.parts[:2] == ("Interface", "Grimoire") and source_size == (400, 600):
        return (560, 840)
    if relative.parts[:3] == ("Interface", "MiniMenu", "800x600") and source_size == (600, 400):
        return (840, 560)
    if relative.parts[:2] == ("Interface", "ProgressIndicator") and source_size == (600, 36):
        return (840, 50)
    return None


def assets() -> list[Path]:
    result = []
    for path in sorted((ROOT / "Interface").rglob("*")):
        relative = path.relative_to(ROOT)
        if path.suffix.lower() == ".cfg" and (RECT2.search(path.read_bytes()) or NAMED.search(path.read_bytes())):
            result.append(relative)
        elif path.suffix.lower() in (".jpg", ".jpeg", ".bmp"):
            with Image.open(path) as image:
                if target_image_size(relative, image.size):
                    result.append(relative)
    # An already-fitted image is tracked by state and is recovered from backup.
    return result


def fit_image(relative: Path, original: bytes) -> tuple[bytes, str]:
    with Image.open(io.BytesIO(original)) as base_image:
        expected = target_image_size(relative, base_image.size)
    if expected is None:
        raise RuntimeError(f"Unsupported source UI dimensions: {relative}")
    with Image.open(io.BytesIO(original)) as image:
        image = image.convert("RGB").resize(expected, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        if relative.suffix.lower() == ".bmp":
            image.save(buffer, "BMP")
        else:
            image.save(buffer, "JPEG", quality=100, subsampling=0)
    return buffer.getvalue(), "source-resize"


def apply(enabled: bool) -> dict:
    gate()
    if not enabled:
        restore_keyed_bmps()
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else None
    migration_start = None
    if state:
        paths = [Path(row["path"]) for row in state["files"]]
        current = [(ROOT / path).read_bytes() for path in paths]
        if [sha(data) for data in current] != [row["applied_sha256"] for row in state["files"]]:
            raise RuntimeError("UI files changed outside fit tool")
        originals = [(BACKUP / str(index)).read_bytes() for index in range(len(paths))]
        if [sha(data) for data in originals] != [row["original_sha256"] for row in state["files"]]:
            raise RuntimeError("UI backup hash mismatch")
        if enabled:
            migration_start = len(paths)
            known = set(paths)
            for path in (candidate for candidate in assets() if candidate not in known):
                original = (ROOT / path).read_bytes()
                paths.append(path)
                originals.append(original)
                (BACKUP / str(len(paths) - 1)).write_bytes(original)
    else:
        if not enabled:
            return {"enabled": False, "files": 0}
        # Migrate the earlier one-screen fit once. Its own backup remains intact.
        apply_old_menu_fit(False)
        paths = assets()
        originals = [(ROOT / path).read_bytes() for path in paths]
        BACKUP.mkdir(parents=True, exist_ok=True)
        for index, data in enumerate(originals):
            (BACKUP / str(index)).write_bytes(data)
    if not enabled:
        for path, data in zip(paths, originals):
            (ROOT / path).write_bytes(data)
        STATE.unlink()
        return {"enabled": False, "files": len(paths)}
    if state and migration_start == len(paths):
        return state
    next_files = list(state["files"]) if state else []
    outputs = []
    selected_paths = paths[migration_start:] if state else paths
    selected_originals = originals[migration_start:] if state else originals
    for path, original in zip(selected_paths, selected_originals):
        if path.suffix.lower() == ".cfg":
            data, rect_count, named_count = fit_cfg(original)
            provenance = f"layout: {rect_count} Rect2, {named_count} named coordinates"
        else:
            data, provenance = fit_image(path, original)
        outputs.append(data)
        next_files.append({"path": path.as_posix(), "original_sha256": sha(original),
                           "applied_sha256": sha(data), "provenance": provenance})
    for path, data in zip(selected_paths, outputs):
        (ROOT / path).write_bytes(data)
    report = {"enabled": True, "legacy_size": LEGACY_SIZE, "native_size": NATIVE_SIZE,
              "files": next_files}
    STATE.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def restore_keyed_bmps() -> None:
    if not KEYED_STATE.exists():
        return
    rows = json.loads(KEYED_STATE.read_text(encoding="utf-8"))["files"]
    for row in rows:
        path = ROOT / row["path"]
        if not path.exists() or sha(path.read_bytes()) != row["sha256"]:
            raise RuntimeError("Keyed BMP changed outside tool")
    for row in rows:
        (ROOT / row["path"]).unlink()
    KEYED_STATE.unlink()


def keyed_bmps() -> dict:
    state = apply(True)
    if KEYED_STATE.exists():
        rows = json.loads(KEYED_STATE.read_text(encoding="utf-8"))["files"]
        if any(sha((ROOT / row["path"]).read_bytes()) != row["sha256"] for row in rows):
            raise RuntimeError("Keyed BMP changed outside tool")
        return {"keyed_bmps": len(rows)}
    records = {row["source"].lower(): row for row in
               json.loads(SNAPSHOT.read_text(encoding="utf-8"))["records"]}
    outputs, rows = [], []
    for index, row in enumerate(state["files"]):
        relative = Path(row["path"])
        if relative.parts[:3] != ("Interface", "Grimoire", "800x600") or relative.suffix.lower() not in (".jpg", ".jpeg"):
            continue
        with Image.open(io.BytesIO((BACKUP / str(index)).read_bytes())) as handle:
            source = handle.convert("RGB")
        if source.size != (400, 600):
            continue
        target = ROOT / relative.with_suffix(".BMP")
        if target.exists():
            raise RuntimeError("Existing keyed BMP would be overwritten")
        record = records.get(relative.as_posix().lower())
        size = (560, 840)
        if record:
            png = PACK / record["output"]
            manifest = json.loads(png.with_suffix(png.suffix + ".json").read_text(encoding="utf-8"))
            if sha(png.read_bytes()) != record["output_sha256"] or manifest["output_sha256"] != record["output_sha256"]:
                raise RuntimeError("Generated keyed page hash mismatch: " + row["path"])
            with Image.open(png) as handle:
                generated = handle.convert("RGB").resize(size, Image.Resampling.LANCZOS)
            provenance = "verified-qwen-source-template-bmp"
        else:
            generated = source.resize(size, Image.Resampling.LANCZOS)
            provenance = "source-resize-source-template-bmp"
        template = qwen_canvas.grimoire_key_template(source)
        clean = qwen_canvas.apply_grimoire_key_template(generated, template)
        buffer = io.BytesIO()
        clean.save(buffer, "BMP")
        data = buffer.getvalue()
        outputs.append((target, data))
        next_row = {"path": target.relative_to(ROOT).as_posix(), "sha256": sha(data),
                    "source_sha256": row["original_sha256"], "provenance": provenance,
                    "key_edge_policy": "grimoire-source-template-v2"}
        if record:
            next_row["qwen_png_sha256"] = record["output_sha256"]
            next_row["manager_job_id"] = manifest["manager_job_id"]
        rows.append(next_row)
    for path, data in outputs:
        path.write_bytes(data)
    KEYED_STATE.write_text(json.dumps({"files": rows}, indent=2) + "\n", encoding="utf-8")
    return {"keyed_bmps": len(rows)}


SAMPLES = (
    "Interface/MainScreen/800x600/Main Menu 800-600.JPG",
    "Interface/BattleOptionsScreen/800x600/Battle Options Screen 800-600.JPG",
    "Interface/LoadGame/800x600/Load Game 800-600.JPG",
)


def samples(enabled: bool) -> dict:
    state = apply(True)  # validates every current file and original backup
    records = {row["source"].lower(): row for row in
               json.loads(SNAPSHOT.read_text(encoding="utf-8"))["records"]}
    outputs = []
    for index, row in enumerate(state["files"]):
        if row["path"] not in SAMPLES:
            continue
        original = (BACKUP / str(index)).read_bytes()
        if enabled:
            record = records[row["path"].lower()]
            png = PACK / record["output"]
            manifest = json.loads(png.with_suffix(png.suffix + ".json").read_text(encoding="utf-8"))
            if sha(png.read_bytes()) != record["output_sha256"] or manifest["output_sha256"] != record["output_sha256"]:
                raise RuntimeError("Generated output hash mismatch: " + row["path"])
            with Image.open(io.BytesIO(original)) as source:
                if qwen_canvas.detect_key_mask(source.convert("RGB"))[1] is not None:
                    raise RuntimeError("Sample replacement requires an unkeyed source")
            with Image.open(png) as source:
                if source.format != "PNG" or list(source.size) != record["target_size"]:
                    raise RuntimeError("Generated dimensions or format mismatch")
                buffer = io.BytesIO()
                source.convert("RGB").resize(NATIVE_SIZE, Image.Resampling.LANCZOS).save(
                    buffer, "JPEG", quality=100, subsampling=0)
            data = buffer.getvalue()
            row["provenance"] = "verified-qwen-sample"
            row["generated_png_sha256"] = record["output_sha256"]
            row["manager_job_id"] = manifest["manager_job_id"]
        else:
            data, row["provenance"] = fit_image(Path(row["path"]), original)
            row.pop("generated_png_sha256", None)
            row.pop("manager_job_id", None)
        row["applied_sha256"] = sha(data)
        outputs.append((ROOT / row["path"], data))
    if len(outputs) != len(SAMPLES):
        raise RuntimeError("Sample backgrounds missing from layout state")
    for path, data in outputs:
        path.write_bytes(data)
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    if enabled:
        SAMPLE_SELECTION.write_text(json.dumps({"enabled": True, "samples": list(SAMPLES)}, indent=2) + "\n",
                                    encoding="utf-8")
    else:
        SAMPLE_SELECTION.unlink(missing_ok=True)
    return {"generated_samples": enabled, "files": len(outputs)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("fit", "restore", "samples", "restore-samples", "keyed-bmps"))
    mode = parser.parse_args().mode
    if mode == "keyed-bmps":
        print(json.dumps(keyed_bmps(), indent=2))
    elif "samples" in mode:
        print(json.dumps(samples(mode == "samples"), indent=2))
    else:
        result = apply(mode == "fit")
        print(json.dumps({"enabled": result["enabled"], "files": len(result["files"]) if isinstance(result["files"], list) else result["files"]}, indent=2))
