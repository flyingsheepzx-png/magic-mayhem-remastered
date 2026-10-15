"""Hash-gated Chinese glyph scaling in the isolated native UI runtime."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct

import capstone
import pefile

from hd_font_probe import PROBE, ROOT, read_sft


SOURCE_DLL_SHA = "b627c7483b65ed84aacfc2120f629ce9bd367ab175b2c5a2203060d1df3eeca4"
CLEAR_SITES = (0x4A5D77, 0x4A5F2D, 0x4A606C, 0x4A61EB, 0x4A63AB,
               0x4A6500, 0x4A66AF, 0x4A6878, 0x4A6983)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def coff_function(path: Path) -> bytes:
    raw = path.read_bytes()
    machine, count, _, symbols, symbol_count, optional_size, _ = struct.unpack_from("<HHIIIHH", raw)
    if machine != 0x14C or optional_size != 0:
        raise ValueError("Expected x86 COFF")
    text = []
    for i in range(count):
        section = struct.unpack_from("<8sIIIIIIHHI", raw, 20 + i * 40)
        name, _, _, size, offset, reloc, _, reloc_count, _, _ = section
        if name.startswith(b".text"):
            if reloc_count or reloc:
                raise ValueError("Font function must have no imports or relocations")
            text.append(raw[offset:offset + size])
    if len(text) != 1 or not text[0]:
        raise ValueError("Expected one self-contained font function")
    return text[0]


def chinese_dll(source: bytes, function: bytes) -> tuple[bytes, dict]:
    if sha(source) != SOURCE_DLL_SHA:
        raise ValueError("Unknown Chinese translation DLL")
    pe = pefile.PE(data=source)
    if pe.OPTIONAL_HEADER.ImageBase != 0x400000 or pe.FILE_HEADER.Machine != 0x14C:
        raise ValueError("Unknown translation PE layout")
    out = bytearray(source)
    section_rva = align(pe.OPTIONAL_HEADER.SizeOfImage, pe.OPTIONAL_HEADER.SectionAlignment)
    helper_rva = section_rva + 64
    scratch_rva = align(helper_rva + len(function), pe.OPTIONAL_HEADER.SectionAlignment)
    # The shim keeps the DLL's original lookup, GB encoding and native cache.
    # call/pop obtains a module-relative pointer even when the DLL is relocated.
    shim = bytearray(bytes.fromhex("55 8b ec ff 75 08"))
    shim += b"\xe8" + struct.pack("<i", 0x1670 - (section_rva + len(shim) + 5))
    shim += bytes.fromhex("83 c4 04 e8 00 00 00 00")
    popped_rva = section_rva + len(shim)
    shim += bytes.fromhex("5a 85 c0 75 06 8d 82") + struct.pack("<i", 0x53768 - popped_rva)
    shim += bytes.fromhex("81 c2") + struct.pack("<i", scratch_rva - popped_rva)
    shim += bytes.fromhex("52 50")
    shim += b"\xe8" + struct.pack("<i", helper_rva - (section_rva + len(shim) + 5))
    shim += bytes.fromhex("83 c4 08 8b e5 5d c3")
    if len(shim) > 64:
        raise ValueError("Shim overlap")
    code = shim + b"\x90" * (64 - len(shim)) + function
    code_offset = align(len(out), pe.OPTIONAL_HEADER.FileAlignment)
    code_raw_size = align(len(code), pe.OPTIONAL_HEADER.FileAlignment)
    out.extend(b"\0" * (code_offset - len(out)))
    out.extend(code)
    out.extend(b"\0" * (code_raw_size - len(code)))
    section_header = pe.sections[-1].get_file_offset() + 40
    if section_header + 80 > pe.sections[0].PointerToRawData:
        raise ValueError("No room for font section headers")
    # Executable code and writable scratch are separate PE sections.
    struct.pack_into("<8sIIIIIIHHI", out, section_header,
                     b".hdcf\0\0\0", len(code), section_rva, code_raw_size, code_offset,
                     0, 0, 0, 0, 0x60000020)
    struct.pack_into("<8sIIIIIIHHI", out, section_header + 40,
                     b".hdfb\0\0\0", 32768, scratch_rva, 0, 0,
                     0, 0, 0, 0, 0xC0000080)
    struct.pack_into("<H", out, pe.FILE_HEADER.get_field_absolute_offset("NumberOfSections"), pe.FILE_HEADER.NumberOfSections + 2)
    struct.pack_into("<I", out, pe.OPTIONAL_HEADER.get_field_absolute_offset("SizeOfImage"), scratch_rva + 32768)
    struct.pack_into("<I", out, pe.OPTIONAL_HEADER.get_field_absolute_offset("SizeOfCode"), pe.OPTIONAL_HEADER.SizeOfCode + code_raw_size)
    struct.pack_into("<I", out, pe.OPTIONAL_HEADER.get_field_absolute_offset("SizeOfUninitializedData"), pe.OPTIONAL_HEADER.SizeOfUninitializedData + 32768)
    site = pe.get_offset_from_rva(0x123C)
    before = source[site:site + 7]
    if before != bytes.fromhex("55 8b ec 66 8b 45 08"):
        raise ValueError("Unknown native Chinese glyph lookup entry")
    after = b"\xe9" + struct.pack("<i", section_rva - 0x1241) + b"\x90\x90"
    out[site:site + 7] = after
    verification = pefile.PE(data=bytes(out))
    if verification.sections[-2].VirtualAddress != section_rva or verification.sections[-1].Misc_VirtualSize != 32768:
        raise ValueError("Invalid patched translation PE")
    return bytes(out), {"site_rva": "0x123c", "before": before.hex(), "after": after.hex(),
                        "code_rva": hex(section_rva), "helper_rva": hex(helper_rva),
                        "scratch_rva": hex(scratch_rva), "scratch_bytes": 32768,
                        "function_sha256": sha(function)}


def stage() -> None:
    build_path = PROBE / "build.json"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    if "chinese_fonts" in build or (PROBE / "before-chinese-fonts").exists():
        raise ValueError("Chinese font probe already staged")
    engine = PROBE / "runtime/Chaos-Wide169-engine.exe"
    dll = PROBE / "runtime/chaos95.dll"
    original_engine, original_dll = engine.read_bytes(), dll.read_bytes()
    if sha(original_engine) != build["patched_engine_sha256"]:
        raise ValueError("Native UI probe engine changed")
    manifest = json.loads((Path(build["source_package"]) / "manifest.json").read_text(encoding="utf-8"))
    if manifest["files"]["chaos95.dll"] != SOURCE_DLL_SHA:
        raise ValueError("Latest package has another translation DLL")
    for path in (PROBE / "runtime/Sprites").glob("*.sft"):
        read_sft(path.read_bytes())
    function = coff_function(ROOT / "modernization/build/native_ui_font.obj")
    output_dll, report = chinese_dll(original_dll, function)
    pe = pefile.PE(data=original_engine)
    output_engine = bytearray(original_engine)
    changes = []
    for va in CLEAR_SITES:
        off = pe.get_offset_from_rva(va - 0x400000)
        before = bytes.fromhex("b9 20 00 00 00")
        after = bytes.fromhex("b9 40 00 00 00")
        if original_engine[off:off + 5] != before:
            raise ValueError(f"Unknown font row clearing at {va:#x}")
        output_engine[off:off + 5] = after
        changes.append({"va": hex(va), "before": before.hex(), "after": after.hex()})
    backup = PROBE / "before-chinese-fonts"
    backup.mkdir()
    (backup / "Chaos-Wide169-engine.exe").write_bytes(original_engine)
    (backup / "chaos95.dll").write_bytes(original_dll)
    (backup / "build.json").write_bytes(build_path.read_bytes())
    dll.write_bytes(output_dll)
    engine.write_bytes(output_engine)
    report.update({"source_dll_sha256": sha(original_dll), "patched_dll_sha256": sha(output_dll),
                   "engine_before_sha256": sha(original_engine), "engine_after_sha256": sha(output_engine),
                   "row_clearing": changes, "scale": 2})
    build["chinese_fonts"] = report
    build["patched_engine_sha256"] = sha(output_engine)
    build_path.write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    stage()
