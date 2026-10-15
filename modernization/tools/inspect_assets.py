"""Inventory installed game assets without modifying them."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct
import wave

from PIL import Image

ASSET_DIRS = ("AI", "Bitmaps", "CFG", "Creatures", "Cursors", "FMV", "Interface", "Music", "Portraits", "Realms", "Sounds", "SpeechBox", "Sprites", "Text", "Wizards")
RASTER = {".bmp", ".jpg", ".jpeg", ".pcx", ".png", ".tga"}
MAGIC = {".spr": b"SPR\0", ".ani": b"ANI\0", ".sft": b"SFT\0"}


def sha256(path: Path) -> str:
    hash_ = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hash_.update(chunk)
    return hash_.hexdigest()


def classify(rel: Path) -> str:
    folder, ext = rel.parts[0].lower(), rel.suffix.lower()
    if folder == "interface": return "ui"
    if ext == ".sft" or rel.name.lower() == "egfonts.enc": return "font"
    if ext == ".avi": return "fmv"
    if ext in {".ogg", ".wav"}: return "audio"
    if ext in {".ani", ".spr"}: return "animation-sprite"
    if ext == ".cur" or folder == "cursors": return "cursor"
    if folder in {"bitmaps", "portraits"}: return "static-art"
    if folder == "realms" or ext in {".map", ".mps", ".nod", ".evt", ".tag", ".cid"}: return "world-data"
    if folder in {"creatures", "wizards", "sprites"}: return "gameplay-art"
    if folder in {"ai", "cfg", "text"}: return "configuration-text"
    return "other"


def inspect(root: Path, path: Path) -> dict:
    rel = path.relative_to(root)
    rec = {"path": rel.as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path), "extension": path.suffix.lower() or "<none>", "purpose": classify(rel)}
    with path.open("rb") as stream: head = stream.read(8192)
    ext = path.suffix.lower()
    rec.update(signature_hex=head[:12].hex(), inspect_status="opaque")
    if ext in RASTER or ext == ".cur":
        try:
            with Image.open(path) as im:
                rec.update(format=im.format, mode=im.mode, width=im.width, height=im.height)
                im.verify()
            rec["inspect_status"] = "decoded-metadata"
        except (OSError, ValueError) as exc:
            rec.update(inspect_status="decode-failed", inspect_error=str(exc))
    elif ext in MAGIC:
        rec.update(magic_matches=head.startswith(MAGIC[ext]), inspect_status="header-only")
        if ext == ".ani":
            refs = sorted(set(m.group(0).decode("ascii", errors="ignore") for m in re.finditer(rb"[A-Za-z0-9 _.-]+\.spr", head, flags=re.I)))
            if refs: rec["sprite_refs_header"] = refs
    elif ext == ".avi":
        if head.startswith(b"RIFF") and head[8:12] == b"AVI ":
            offset = head.find(b"avih")
            if offset >= 0 and len(head) >= offset + 48:
                vals = struct.unpack_from("<10I", head, offset + 8)
                rec.update(width=vals[8], height=vals[9], frame_count=vals[4], stream_count=vals[6], nominal_fps=round(1_000_000 / vals[0], 3) if vals[0] else None)
            rec["inspect_status"] = "riff-header-only"
        else: rec["inspect_status"] = "unexpected-header"
    elif ext == ".wav":
        try:
            with wave.open(str(path), "rb") as wav:
                rec.update(channels=wav.getnchannels(), sample_rate=wav.getframerate(), sample_count=wav.getnframes())
            rec["inspect_status"] = "wave-header"
        except (wave.Error, OSError) as exc: rec.update(inspect_status="header-failed", inspect_error=str(exc))
    elif ext == ".ogg": rec["inspect_status"] = "ogg-header" if head.startswith(b"OggS") else "unexpected-header"
    return rec


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=(Path(__file__).resolve().parents[2] / "game"))
    parser.add_argument("--output", type=Path, required=True, help="Local full manifest JSON")
    parser.add_argument("--summary", type=Path, help="Small aggregate summary JSON")
    args = parser.parse_args()
    root = args.root.resolve()
    paths = [p for name in ASSET_DIRS for p in (root / name).rglob("*") if p.is_file()]
    if (root / "Egfonts.enc").is_file(): paths.append(root / "Egfonts.enc")
    records = [inspect(root, path) for path in sorted(paths, key=lambda p: str(p).casefold())]
    by_ext, by_purpose = Counter(rec["extension"] for rec in records), Counter(rec["purpose"] for rec in records)
    by_folder = Counter(rec["path"].split("/")[0] for rec in records)
    dimensions = Counter(f'{rec["width"]}x{rec["height"]}' for rec in records if rec["purpose"] == "ui" and "width" in rec)
    pairs = defaultdict(set)
    for rec in records:
        parts = rec["path"].split("/")
        if parts[0] == "Interface" and len(parts) > 3 and parts[2].lower() in {"640x480", "800x600"}:
            pairs[(parts[1].casefold(), parts[3].casefold())].add(parts[2].lower())
    summary = {
        "schema": 2, "asset_directories": list(ASSET_DIRS), "file_count": len(records),
        "total_bytes": sum(rec["bytes"] for rec in records),
        "by_extension": dict(sorted(by_ext.items())), "by_purpose": dict(sorted(by_purpose.items())),
        "by_folder": dict(sorted(by_folder.items())), "ui_dimensions": dict(sorted(dimensions.items())),
        "ui_matching_640_800_name_pairs": sum(len(s) == 2 for s in pairs.values()),
        "ui_single_resolution_name_groups": sum(len(s) == 1 for s in pairs.values()),
        "format_status": dict(sorted(Counter(rec["inspect_status"] for rec in records).items())),
        "sprite_animation_magic_mismatch": sum(rec.get("magic_matches") is False for rec in records),
        "ani_with_header_sprite_reference": sum(bool(rec.get("sprite_refs_header")) for rec in records),
        "note": "Header observations are not validated SPR/ANI decoding or frame counts.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"schema": 2, "root": str(root), "files": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
