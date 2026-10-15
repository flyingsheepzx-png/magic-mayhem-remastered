"""Build the isolated 1120x840 viewport with the original HUD anchored bottom right.

Each site was traced in the community EXE. The original 640-to-800 HUD adds
(160,120); this dedicated high-resolution sibling adds another (320,240).
The original EXE and the original two selectable modes remain separate.
"""

import hashlib
import json
from pathlib import Path
import struct

import capstone
import pefile

from hd_surface_lab_build import PATCHES, RECT_PATCHES, SOURCE_SHA, ROOT

# instruction VA: (mnemonic, old constant, displacement added, semantic label)
HUD_SITES = {
    0x469C31: ("add", 640, 320, "scroll right edge width"),
    0x469C4A: ("add", 479, 240, "scroll bottom edge maximum"),
    0x469C78: ("add", 480, 240, "scroll left edge direction quarters"),
    0x469CC3: ("add", 480, 240, "scroll right edge direction quarters"),
    0x469D6E: ("add", 479, 240, "scroll bottom direction edge"),
    0x4A7181: ("add", 640, 320, "main menu backing surface width"),
    0x4A7192: ("add", 480, 240, "main menu backing surface height"),
    0x47107E: ("add", 470, 320, "roof visibility button X"),
    0x471091: ("add", 388, 240, "roof visibility button Y"),
    0x4D2E70: ("add", 520, 320, "wizard meter local origin X"),
    0x4D2E8B: ("add", 340, 240, "wizard meter local origin Y"),
    0x4D377D: ("add", 520, 320, "wizard initial rect X"),
    0x4D3791: ("add", 340, 240, "wizard initial rect Y"),
    0x4D37CE: ("add", 520, 320, "wizard refreshed rect X"),
    0x4D37E9: ("add", 340, 240, "wizard refreshed rect Y"),
    0x4D5E66: ("add", 436, 320, "spellbox anchor X"),
    0x4D5F01: ("lea", 430, 240, "spellbox first button Y"),
    0x4D5FC4: ("add", 344, 240, "spellbox second button Y"),
    0x4D609B: ("add", 386, 240, "spellbox third button Y"),
    0x4D616F: ("add", 436, 240, "spellbox lower button Y"),
    0x4D4C7D: ("add", 430, 240, "spellbox icon row Y"),
    0x4D4CE8: ("add", 480, 240, "spellbox wrapped rows Y"),
    0x4D6495: ("add", 480, 240, "spellbox backing right Y"),
    0x4D64A9: ("add", 436, 320, "spellbox backing right X"),
    0x4D655D: ("add", 480, 240, "spellbox backing left Y"),
    0x4DE404: ("add", 302, 240, "control-limit icon Y"),
    0x4DE416: ("add", 544, 320, "control-limit icon X"),
    0x4DE689: ("add", 322, 240, "control-limit counter Y"),
    0x4DE69B: ("add", 554, 320, "control-limit counter X"),
    0x4DE9A0: ("add", 322, 240, "control-limit counter refresh Y"),
    0x4DE9B2: ("add", 554, 320, "control-limit counter refresh X"),
    0x4A45FD: ("add", 640, 320, "cursor surface clipping width"),
    0x4A460E: ("add", 480, 240, "cursor surface clipping height"),
    0x4A49AB: ("add", 640, 320, "mouse cursor dirty width"),
    0x4A49C2: ("add", 480, 240, "mouse cursor dirty height"),
    0x4A4B26: ("add", 640, 320, "cursor restore rectangle right"),
    0x4A4B4B: ("add", 480, 240, "cursor restore rectangle bottom"),
    0x4A4C77: ("add", 640, 320, "cursor redraw clip right"),
    0x4A4C9F: ("add", 480, 240, "cursor redraw clip bottom"),
    0x4E422F: ("add", 640, 320, "primary cursor backing surface width"),
    0x4E4245: ("add", 480, 240, "primary cursor backing surface height"),
    0x4E8FE0: ("add", 640, 320, "window/input logical width global"),
    0x4E8FF3: ("add", 480, 240, "window/input logical height global"),
    0x4E9089: ("add", 640, 320, "window client rect width"),
    0x4E909F: ("add", 480, 240, "window client rect height"),
    0x4E9131: ("add", 640, 320, "fullscreen window rect width"),
    0x4E9142: ("add", 480, 240, "fullscreen window rect height"),
    0x4D93BF: ("add", 604, 320, "enemy warning first-column left"),
    0x4D94B1: ("add", 640, 320, "enemy warning row right edge"),
    0x4D962E: ("add", 640, 320, "enemy warning overlay right edge"),
    0x4D972D: ("add", 568, 320, "enemy warning second-column left"),
    0x4DB836: ("add", 480, 240, "battle tooltip bottom bound"),
    0x4DB88E: ("add", 640, 320, "battle tooltip right bound"),
    0x4DB8B8: ("add", 480, 240, "battle tooltip secondary bottom bound"),
    0x573A1E: ("add", 640, 320, "speech continuation click width"),
    0x573A35: ("add", 480, 240, "speech continuation click height"),
    0x46AA8E: ("add", 444, 226, "loading bar bottom anchor"),
    0x46AA9E: ("add", 42, 80, "loading bar horizontal centring remainder"),
    0x47096B: ("add", 444, 226, "loading bar bottom anchor"),
    0x47097D: ("add", 42, 80, "loading bar horizontal centring remainder"),
    0x4713B5: ("add", 444, 226, "loading bar bottom anchor"),
    0x4713C9: ("add", 42, 80, "loading bar horizontal centring remainder"),
    0x471B16: ("add", 444, 226, "loading bar bottom anchor"),
    0x471B28: ("add", 42, 80, "loading bar horizontal centring remainder"),
    0x4DC4E7: ("mov", 598, 239, "loading bar active width"),
    0x4DC4EF: ("mov", 36, 14, "loading bar active height"),
    0x4DC548: ("mov", 598, 239, "loading bar desaturated width"),
    0x4DC550: ("mov", 36, 14, "loading bar desaturated height"),
    0x4DC56B: ("mov", 598, 239, "loading bar step numerator"),
    0x4DC575: ("mov", 36, 14, "loading bar draw height"),
    0x4DC611: ("mov", 598, 239, "loading bar completed width"),
    0x4DC622: ("cmp", 598, 239, "loading bar width limit"),
    0x4DC62A: ("mov", 598, 239, "loading bar width clamp"),
}


# Grimoire uses two 400x600 pages and a separate 800x600 backing. The
# sibling expands those to 560x840 pages on a 1120x840 backing.
GRIMOIRE_SITES = {
    0x4C52C1: ("add", 640, 320, "Grimoire backing width"),
    0x4C52D4: ("add", 480, 240, "Grimoire backing height"),
    0x4C3DF0: ("add", 640, 320, "Grimoire left page canvas width"),
    0x4C3DFE: ("cmp", 800, 320, "Grimoire left page high-res branch"),
    0x4C3E06: ("mov", 400, 160, "Grimoire left page half width"),
    0x4C3E2D: ("add", 480, 240, "Grimoire left page bottom"),
    0x4C3E8A: ("add", 640, 320, "Grimoire right page canvas width"),
    0x4C3E98: ("cmp", 800, 320, "Grimoire right page high-res branch"),
    0x4C3EA0: ("mov", 400, 160, "Grimoire right page half width"),
    0x4C3EBC: ("add", 480, 240, "Grimoire right page bottom"),
    0x4C5B08: ("add", 640, 320, "Grimoire page asset canvas width"),
    0x4C5B16: ("cmp", 800, 320, "Grimoire page asset high-res branch"),
    0x4C5B29: ("mov", 400, 160, "Grimoire page asset width"),
    0x4C5B51: ("add", 480, 240, "Grimoire page asset height"),
    0x4C5B9C: ("add", 640, 320, "Grimoire second-page offset canvas width"),
    0x4C5BA8: ("cmp", 800, 320, "Grimoire second-page offset high-res branch"),
    0x4C5BB3: ("mov", 400, 160, "Grimoire second-page offset"),
    0x4C57CB: ("add", 640, 320, "Grimoire page draw canvas width"),
    0x4C57D7: ("cmp", 800, 320, "Grimoire page draw high-res branch"),
    0x4C57DE: ("mov", 400, 160, "Grimoire page draw half width"),
    0x4C5801: ("cmp", 800, 320, "Grimoire page clip high-res branch"),
    0x4C5808: ("mov", 400, 160, "Grimoire page clip half width"),
    0x4C5A22: ("add", 640, 320, "Grimoire page width helper canvas"),
    0x4C5A30: ("cmp", 800, 320, "Grimoire page width helper high-res branch"),
    0x4C5A43: ("mov", 400, 160, "Grimoire page width helper"),

}


# The final display/turn animation at 0x4C5C20..0x4C6680 copies the two
# pages to the primary surface. Its rectangles are separate from page allocation.
GRIMOIRE_DRAW_GROUPS = (
    (0x4C60D0, 0x4C60DE, 0x4C60E6, 0x4C6105),
    (0x4C615A, 0x4C6168, 0x4C6170, 0x4C619F),
    (0x4C61F3, 0x4C6201, 0x4C6209, 0x4C6226),
    (0x4C6282, 0x4C6290, 0x4C6298, 0x4C62B5),
    (0x4C634B, 0x4C6359, 0x4C6361, 0x4C6380),
    (0x4C63D5, 0x4C63E3, 0x4C63EB, 0x4C641E),
    (0x4C647C, 0x4C648A, 0x4C6492, 0x4C64AF),
    (0x4C650F, 0x4C651D, 0x4C6525, 0x4C6542),
    (0x4C65C5, 0x4C65D3, 0x4C65DB, 0x4C65FA),
    (0x4C6643, 0x4C664F, 0x4C6656, 0x4C6675),
)
for index, (width, branch, half, height) in enumerate(GRIMOIRE_DRAW_GROUPS):
    for address, mnemonic, old, delta, label in (
        (width, "add", 640, 320, "canvas width"),
        (branch, "cmp", 800, 320, "high-res branch"),
        (half, "mov", 400, 160, "half width"),
        (height, "add", 480, 240, "height"),
    ):
        GRIMOIRE_SITES[address] = (mnemonic, old, delta, f"Grimoire display {index} {label}")


# Verified first width/height pair passed to each full-screen DDSD creator.
# Resource filename formatting uses later, separate 800x600 pairs and stays intact.
FULL_SCREEN_SURFACES = {
    "quick battle menu": (0x4A7EAE, 0x4A7EBF),
    "battle options": (0x4A8ED7, 0x4A8EE8),
    "load game": (0x4A9FE2, 0x4A9FF3),
    "save game": (0x4AB032, 0x4AB043),
    "single player setup": (0x4AC712, 0x4AC723),
    "join multiplayer": (0x4AF232, 0x4AF243),
    "multiplayer select": (0x4B01E2, 0x4B01F3),
    "multiplayer settings": (0x4B1122, 0x4B1133),
    "region entry": (0x4B2C77, 0x4B2C88),
    "character screen": (0x4B4450, 0x4B4464),
    "multiplayer battle setup": (0x4B72B2, 0x4B72C3),
    "map selection": (0x4BB702, 0x4BB713),
    "error screen": (0x4BC304, 0x4BC315),
}
UI_SURFACE_SITES = {
    site: ("add", old, delta, label + " surface " + axis)
    for label, (width_site, height_site) in FULL_SCREEN_SURFACES.items()
    for site, old, delta, axis in ((width_site, 640, 320, "width"),
                                    (height_site, 480, 240, "height"))
}

# These screens keep looking up assets under the original 800x600 directory.
# Only their backing surfaces and interactive bounds grow to 1120x840.
ADDITIONAL_SCREEN_SITES = {
    0x473DE0: ("add", 640, 320, "victory/defeat backing width"),
    0x473DF4: ("add", 480, 240, "victory/defeat backing height"),
    0x473E37: ("add", 639, 320, "victory/defeat interactive right"),
    0x473E4F: ("add", 479, 240, "victory/defeat interactive bottom"),
    0x5778EA: ("add", 640, 320, "portmanteau backing width"),
    0x577905: ("add", 480, 240, "portmanteau backing height"),
    0x577942: ("add", 639, 320, "portmanteau interactive right"),
    0x57795A: ("add", 479, 240, "portmanteau interactive bottom"),
    0x54F6F9: ("add", 640, 320, "realm map backing width"),
    0x54F70D: ("add", 480, 240, "realm map backing height"),
    0x5502AD: ("add", 640, 320, "realm map refreshed backing width"),
    0x5502C8: ("add", 480, 240, "realm map refreshed backing height"),
}


# For Grimoire content, try the engine's existing lossless BMP loader first,
# with the original JPEG as fallback. The community EXE tries JPEG first.
GRIMOIRE_FORMAT_SITES = {
    0x4C5319: (0x5E1F2C, 0x5E1F1C, "Grimoire page BMP-first format"),
    0x4C536A: (0x5E1F1C, 0x5E1F2C, "Grimoire page JPEG fallback"),
}
GRIMOIRE_LOADER_SITES = {
    0x4C532F: (0x58D320, 0x58D1A0, "Grimoire BMP-first decoder"),
    0x4C5380: (0x58D1A0, 0x58D320, "Grimoire JPEG fallback decoder"),
}


# test5: screen-specific coordinates and the sprite-bar's full-surface clip.
TEST5_SITES = {
    0x54FDC0: ("add", 640, 320, "realm toolbar right anchor"),
    0x4DD6FE: ("add", 480, 240, "talisman spritebar clip bottom"),
    0x4DD710: ("add", 640, 320, "talisman spritebar clip right"),
}
# Native 800-mode tables precede the independent 640-mode tables.
TEST5_TABLES = ((0x5F09F0,21),(0x5F0C90,25),(0x5F0FB0,1),
                (0x5F0FD0,1),(0x5F0FF0,1),(0x5F1010,1),(0x5F1030,3))


def build() -> dict:
    marker = json.loads((ROOT / "modernization/assets/hd/HD_LAB.json").read_text(encoding="utf-8-sig"))
    if marker.get("kind") != "isolated-hd-game-lab" or Path(marker["root"]).resolve() != ROOT:
        raise RuntimeError("Refusing outside the isolated HD lab")
    source = (ROOT / "Chaos.exe").read_bytes()
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA:
        raise RuntimeError("Unknown community executable")
    pe = pefile.PE(data=source)
    output = bytearray(source)
    changes = []
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    decoder.detail = True
    for va, (old, new) in (PATCHES | RECT_PATCHES).items():
        offset = pe.get_offset_from_rva(va - 0x400000)
        if source[offset:offset + 4] != struct.pack("<I", old):
            raise RuntimeError(f"Unknown bytes at {va:#x}")
        output[offset:offset + 4] = struct.pack("<I", new)
        changes.append({"va": hex(va), "old": old, "new": new, "label": "surface/viewport"})
    for va, (mnemonic, old, delta, label) in (HUD_SITES | UI_SURFACE_SITES | GRIMOIRE_SITES | ADDITIONAL_SCREEN_SITES | TEST5_SITES).items():
        offset = pe.get_offset_from_rva(va - 0x400000)
        instruction = next(decoder.disasm(source[offset:offset + 15], va, count=1))
        field_offset = instruction.disp_offset if mnemonic == "lea" else instruction.imm_offset
        field_size = instruction.disp_size if mnemonic == "lea" else instruction.imm_size
        if instruction.mnemonic != mnemonic or field_size not in (1, 4):
            raise RuntimeError(f"Unexpected instruction at {va:#x}")
        offset += field_offset
        old_bytes = old.to_bytes(field_size, "little")
        new_value = old + delta
        new_bytes = new_value.to_bytes(field_size, "little")
        if source[offset:offset + field_size] != old_bytes:
            raise RuntimeError(f"Unknown layout constant at {va:#x}")
        output[offset:offset + field_size] = new_bytes
        changes.append({"va": hex(va + field_offset), "old": old, "new": new_value, "label": label})
    for va, (old, new, label) in GRIMOIRE_FORMAT_SITES.items():
        offset = pe.get_offset_from_rva(va - 0x400000)
        instruction = next(decoder.disasm(source[offset:offset + 8], va, count=1))
        if instruction.mnemonic != "push" or instruction.imm_size != 4:
            raise RuntimeError(f"Unexpected format instruction at {va:#x}")
        field = offset + instruction.imm_offset
        if source[field:field + 4] != struct.pack("<I", old):
            raise RuntimeError(f"Unknown Grimoire format pointer at {va:#x}")
        output[field:field + 4] = struct.pack("<I", new)
        changes.append({"va": hex(va + instruction.imm_offset), "old": old,
                        "new": new, "label": label})
    for va, (old, new, label) in GRIMOIRE_LOADER_SITES.items():
        offset = pe.get_offset_from_rva(va - 0x400000)
        instruction = next(decoder.disasm(source[offset:offset + 8], va, count=1))
        if instruction.mnemonic != "call" or instruction.size != 5 or instruction.op_str != hex(old):
            raise RuntimeError(f"Unexpected Grimoire decoder call at {va:#x}")
        old_relative = old - (va + 5)
        if source[offset + 1:offset + 5] != struct.pack("<i", old_relative):
            raise RuntimeError(f"Unknown Grimoire decoder call bytes at {va:#x}")
        output[offset + 1:offset + 5] = struct.pack("<i", new - (va + 5))
        changes.append({"va": hex(va + 1), "old": hex(old), "new": hex(new), "label": label})
    for address,count in TEST5_TABLES:
        for i in range(count*4):
            va = address+i*4
            offset = pe.get_offset_from_rva(va-0x400000)
            old = struct.unpack_from("<i",source,offset)[0]
            if not 0 <= old <= 800:
                raise RuntimeError(f"Unexpected UI table value at {va:#x}")
            new = (old*7+2)//5
            struct.pack_into("<i",output,offset,new)
            changes.append({"va":hex(va),"old":old,"new":new,"label":"portmanteau 800-mode rectangle"})
    target = ROOT / "modernization/build/Chaos-HD-ui-engine.exe"
    built = bytes(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(built)
    report = {"target": str(target), "source_sha256": SOURCE_SHA,
              "sha256": hashlib.sha256(built).hexdigest(), "changes": changes}
    (ROOT / "modernization/assets/hd/hud-build.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
