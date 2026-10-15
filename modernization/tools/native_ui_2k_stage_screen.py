"""Stage a hash-checked full-size UI screen in the isolated native UI probe."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import re
import shutil
import struct

import capstone
import pefile
from PIL import Image

from native_ui_2k_probe import OUT, LAB, ENGINE, ROOT, digest


SCREENS = {
    "single_player_setup": {
        "resource": "Interface/SinglePlayerBattle/800x600/Single player Battle Setup 800-600.JPG",
        "cfg": "Interface/SinglePlayerBattle/screen (Single Player Battle).cfg",
        "sites": (0x4AC712, 0x4AC723),
        "rectangles": 70,
    },
    "map_selection": {
        "resource": "Interface/MapSelectionScreen/800x600/Map Selection Screen 800-600.jpg",
        "cfg": "Interface/MapSelectionScreen/screen (Map Selection Screen).cfg",
        "sites": (0x4BB702, 0x4BB713),
        "rectangles": 4,
    },
    "save_game": {
        "resource": "Interface/SaveGame/800x600/Save Game 800-600.JPG",
        "cfg": "Interface/SaveGame/screen (Save Game).cfg",
        "sites": (0x4AB032, 0x4AB043),
        "rectangles": 7,
    },
}


def stage(name: str) -> None:
    spec = SCREENS[name]
    build_path = OUT / "build.json"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    if name in build:
        raise ValueError(name + " already staged")
    engine_raw = ENGINE.read_bytes()
    if digest(engine_raw) != build["patched_engine_sha256"]:
        raise ValueError("Probe engine changed")
    resource, cfg_path = Path(spec["resource"]), Path(spec["cfg"])
    queue = json.loads((ROOT / "modernization/assets/hd/hd-queue.json").read_text(encoding="utf-8"))
    record = next(row for row in queue["records"] if row["source"] == resource.as_posix())
    qwen = ROOT / "modernization/assets/hd/pack" / record["output"]
    raw = qwen.read_bytes()
    manifest = json.loads(qwen.with_suffix(".png.json").read_text(encoding="utf-8"))
    if (record["status"] != "done" or digest(raw) != record["output_sha256"]
            or manifest["source_sha256"] != record["source_sha256"]):
        raise ValueError("Unverified Qwen image")
    with Image.open(io.BytesIO(raw)) as image:
        if image.format != "PNG" or image.size != (1920, 1440):
            raise ValueError("Wrong full-size UI raster")
        framed = Image.new("RGB", (2560, 1440))
        framed.paste(image.convert("RGB"), (320, 0))
    buffer = io.BytesIO()
    framed.save(buffer, "JPEG", quality=100, subsampling=0)
    cfg = (LAB / cfg_path).read_bytes()
    def scale_rect(match: re.Match[bytes]) -> bytes:
        return match[1] + b",".join(str(2 * int(match[i])).encode() for i in range(2, 6))
    scaled, count = re.subn(rb"(?m)^(\s*Rect2\s*=\s*)(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)", scale_rect, cfg)
    if count != spec["rectangles"]:
        raise ValueError(f"Unexpected control rectangle count: {count}")
    pe = pefile.PE(data=engine_raw)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    decoder.detail = True
    patched = bytearray(engine_raw)
    changes = []
    for va, old, new in zip(spec["sites"], (1120, 600), (2400, 1320)):
        offset = pe.get_offset_from_rva(va - 0x400000)
        ins = next(decoder.disasm(engine_raw[offset:offset + 15], va, 1))
        if ins.mnemonic != "add" or ins.imm_size != 4:
            raise ValueError(f"Unknown DDSD instruction: {va:#x}")
        field = offset + ins.imm_offset
        if engine_raw[field:field + 4] != struct.pack("<I", old):
            raise ValueError(f"Unknown surface size: {va:#x}")
        patched[field:field + 4] = struct.pack("<I", new)
        changes.append({"va": hex(va + ins.imm_offset), "old": old, "new": new})
    backup = OUT / ("before-" + name.replace("_", "-"))
    if backup.exists():
        raise ValueError("Backup path already exists")
    backup.mkdir()
    for relative in (Path(ENGINE.name), resource, cfg_path):
        target = backup / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LAB / relative, target)
    ENGINE.write_bytes(patched)
    (LAB / resource).write_bytes(buffer.getvalue())
    (LAB / cfg_path).write_bytes(scaled)
    build[name] = {"qwen_png_sha256": digest(raw),
                   "framed_jpeg_sha256": digest(buffer.getvalue()),
                   "cfg_sha256": digest(scaled),
                   "engine_before_sha256": digest(engine_raw),
                   "rectangles": count, "changes": changes}
    build["patched_engine_sha256"] = digest(patched)
    build_path.write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(build[name], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", choices=SCREENS)
    stage(parser.parse_args().name)
