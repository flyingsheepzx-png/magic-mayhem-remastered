"""Stage the isolated native-size Portmanteau shell and its existing hit boxes."""
from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import struct

import capstone
import pefile
from PIL import Image

from hd_hud_build import TEST5_TABLES
from native_ui_2k_probe import OUT, LAB, ENGINE, ROOT, digest


RESOURCE = Path("Interface/SpellBox/800x600/Portmanteau.bmp")


def stage() -> None:
    build_path = OUT / "build.json"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    if "portmanteau" in build:
        raise ValueError("Portmanteau already staged")
    engine = ENGINE.read_bytes()
    if digest(engine) != build["patched_engine_sha256"]:
        raise ValueError("Probe engine changed")
    queue = json.loads((ROOT / "modernization/assets/hd/hd-queue.json").read_text(encoding="utf-8"))
    record = next(row for row in queue["records"] if row["source"] == RESOURCE.as_posix())
    qwen = ROOT / "modernization/assets/hd/pack" / record["output"]
    raw = qwen.read_bytes()
    manifest = json.loads(qwen.with_suffix(".png.json").read_text(encoding="utf-8"))
    if (record["status"] != "done" or digest(raw) != record["output_sha256"]
            or manifest["source_sha256"] != record["source_sha256"]):
        raise ValueError("Unverified Qwen Portmanteau")
    with Image.open(io.BytesIO(raw)) as image:
        if image.format != "PNG" or image.size != (1920, 1440):
            raise ValueError("Wrong Portmanteau art size")
        framed = Image.new("RGB", (2560, 1440))
        framed.paste(image.convert("RGB"), (320, 0))
    buffer = io.BytesIO()
    framed.save(buffer, "BMP")
    pe = pefile.PE(data=engine)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    decoder.detail = True
    patched = bytearray(engine)
    changes = []
    for va, old, new in ((0x5778EA, 1120, 2400), (0x577905, 600, 1320),
                         (0x577942, 1119, 2399), (0x57795A, 599, 1319)):
        offset = pe.get_offset_from_rva(va - 0x400000)
        ins = next(decoder.disasm(engine[offset:offset + 15], va, 1))
        if ins.mnemonic != "add" or ins.imm_size != 4:
            raise ValueError(f"Unknown Portmanteau dimension: {va:#x}")
        field = offset + ins.imm_offset
        if engine[field:field + 4] != struct.pack("<I", old):
            raise ValueError(f"Unexpected Portmanteau dimension: {va:#x}")
        patched[field:field + 4] = struct.pack("<I", new)
        changes.append({"va": hex(va + ins.imm_offset), "old": old, "new": new})
    for va, count in TEST5_TABLES:
        for i in range(count * 4):
            field = pe.get_offset_from_rva(va + 4 * i - 0x400000)
            old = struct.unpack_from("<i", engine, field)[0]
            if not 0 <= old <= 1280:
                raise ValueError(f"Unexpected Portmanteau hit box: {va + i*4:#x}")
            struct.pack_into("<i", patched, field, old * 2)
    backup = OUT / "before-portmanteau"
    if backup.exists():
        raise ValueError("Portmanteau backup already exists")
    backup.mkdir()
    shutil.copy2(ENGINE, backup / ENGINE.name)
    target = backup / RESOURCE
    target.parent.mkdir(parents=True)
    shutil.copy2(LAB / RESOURCE, target)
    ENGINE.write_bytes(patched)
    (LAB / RESOURCE).write_bytes(buffer.getvalue())
    build["portmanteau"] = {"qwen_png_sha256": digest(raw),
                            "framed_bmp_sha256": digest(buffer.getvalue()),
                            "engine_before_sha256": digest(engine),
                            "engine_after_sha256": digest(patched),
                            "rectangles": sum(count for _, count in TEST5_TABLES),
                            "changes": changes}
    build["patched_engine_sha256"] = digest(patched)
    build_path.write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(build["portmanteau"], indent=2))


if __name__ == "__main__":
    stage()
