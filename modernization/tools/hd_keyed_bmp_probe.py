"""Probe the game's same-name BMP fallback for keyed Grimoire JPEGs.

The test uses verified Qwen PNGs, saves exact colour-key pixels to BMP, hides
only the two lab JPEGs while the private-input game trial runs, then restores
the JPEGs even when the trial fails. A disk backup survives an interrupted run.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image

from hd_menu_fit import ROOT, SUPPORTED_EXE
from hd_ui_fit import STATE, BACKUP, PACK, NATIVE_SIZE
from qwen_canvas import detect_key_mask, protect_grimoire_keys

NAMES = tuple(f"Generic{side}0{index}.JPG" for side in "LR" for index in (1, 2, 3))
STATE_FILE = ROOT / "modernization/assets/hd/keyed-bmp-probe.json"
BACKUP_DIR = ROOT / "modernization/assets/hd/backups/keyed-bmp-probe"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def gate() -> dict:
    marker = json.loads((ROOT / "modernization/assets/hd/HD_LAB.json").read_text(encoding="utf-8-sig"))
    if marker.get("kind") != "isolated-hd-game-lab" or Path(marker["root"]).resolve() != ROOT:
        raise RuntimeError("Refusing outside isolated HD lab")
    if digest((ROOT / "Chaos.exe").read_bytes()) != SUPPORTED_EXE:
        raise RuntimeError("Unknown community executable")
    if not STATE.exists():
        raise RuntimeError("Fit UI before the BMP probe")
    return json.loads(STATE.read_text(encoding="utf-8"))


def restore() -> None:
    if not STATE_FILE.exists():
        return
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    for row in state["files"]:
        jpg = ROOT / row["jpg"]
        bmp = ROOT / row["bmp"]
        original = (BACKUP_DIR / row["backup"]).read_bytes()
        if digest(original) != row["jpg_sha256"]:
            raise RuntimeError("Probe backup hash mismatch")
        if bmp.exists() and digest(bmp.read_bytes()) != row["bmp_sha256"]:
            raise RuntimeError("Probe BMP changed outside tool")
        if jpg.exists() and digest(jpg.read_bytes()) != row["jpg_sha256"]:
            raise RuntimeError("Probe JPEG changed outside tool")
        jpg.write_bytes(original)
        bmp.unlink(missing_ok=True)
    STATE_FILE.unlink()


def stage() -> None:
    fit = gate()
    if STATE_FILE.exists():
        raise RuntimeError("Previous probe needs restore first")
    records = {row["source"].lower(): row for row in
               json.loads((ROOT / "modernization/assets/hd/ui-verified-snapshot.json").read_text(encoding="utf-8"))["records"]}
    fitted = {row["path"]: (index, row) for index, row in enumerate(fit["files"])}
    rows, pending = [], []
    for name in NAMES:
        relative = Path("Interface/Grimoire/800x600") / name
        index, fit_row = fitted[relative.as_posix()]
        jpg = ROOT / relative
        if digest(jpg.read_bytes()) != fit_row["applied_sha256"]:
            raise RuntimeError("Fitted JPEG changed outside tool")
        original = (BACKUP / str(index)).read_bytes()
        record = records[relative.as_posix().lower()]
        if digest(original) != record["source_sha256"]:
            raise RuntimeError("Original source or queue hash mismatch")
        png = PACK / record["output"]
        manifest = json.loads(png.with_suffix(png.suffix + ".json").read_text(encoding="utf-8"))
        if digest(png.read_bytes()) != record["output_sha256"] or manifest["output_sha256"] != record["output_sha256"]:
            raise RuntimeError("Qwen output or manifest hash mismatch")
        with Image.open(io.BytesIO(original)) as source_handle:
            source = source_handle.convert("RGB")
        key, mask, _ = detect_key_mask(source)
        if key is None or mask is None:
            raise RuntimeError("Expected a colour-key page")
        with Image.open(png) as handle:
            if handle.format != "PNG" or list(handle.size) != record["target_size"]:
                raise RuntimeError("Qwen output size or format mismatch")
            resized = handle.convert("RGB").resize((560, 840), Image.Resampling.LANCZOS)
        clean = protect_grimoire_keys(resized, source)
        buffer = io.BytesIO()
        clean.save(buffer, format="BMP")
        bmp_data = buffer.getvalue()
        bmp = jpg.with_suffix(".BMP")
        if bmp.exists():
            raise RuntimeError("Existing BMP would be overwritten")
        pending.append((jpg, jpg.read_bytes(), bmp, bmp_data))
        rows.append({"jpg": relative.as_posix(), "bmp": bmp.relative_to(ROOT).as_posix(),
                     "backup": str(len(rows)), "jpg_sha256": digest(jpg.read_bytes()),
                     "bmp_sha256": digest(bmp_data), "qwen_png_sha256": record["output_sha256"]})
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for index, (_, jpg_data, _, _) in enumerate(pending):
        (BACKUP_DIR / str(index)).write_bytes(jpg_data)
    STATE_FILE.write_text(json.dumps({"files": rows}, indent=2) + "\n", encoding="utf-8")
    for jpg, _, bmp, bmp_data in pending:
        bmp.write_bytes(bmp_data)
        jpg.unlink()


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore()
        return 0
    stage()
    try:
        command = [sys.executable, str(Path(__file__).with_name("hd_background_trial.py")),
                   "--present-2k", "--hud-lab", "--region-icons-flow"]
        return subprocess.run(command, cwd=ROOT, check=False).returncode
    finally:
        restore()


if __name__ == "__main__":
    raise SystemExit(main())
