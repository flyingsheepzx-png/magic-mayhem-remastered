"""Stage or restore an isolated main-menu HD image loading trial.

The diagnostic JPEG exists only to test the old engine's existing JPG loader.
It is not an HD pack deliverable; generated pack assets remain PNG.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image

SUPPORTED_EXE = "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"
ASSETS = {
    "menu": (Path("Interface/MainScreen/800x600/Main Menu 800-600.JPG"),
             Path("modernization/assets/hd/pack/Interface/MainScreen/800x600/Main Menu 800-600.png"),
             "6eb30c60852b419a6a0405a98a8ca3418391bea80bfaa8220e745d674581074a"),
    "options": (Path("Interface/BattleOptionsScreen/800x600/Battle Options Screen 800-600.JPG"),
                Path("modernization/assets/hd/pack/Interface/BattleOptionsScreen/800x600/Battle Options Screen 800-600.png"),
                "af2cef15571b712f34357169fd1053bf3d70899332ebff02887ad3c93ba5aa88"),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("install-2k", "install-800", "install-png", "restore", "status"))
    parser.add_argument("--asset", choices=ASSETS, default="menu")
    parser.add_argument("--root", type=Path, default=(Path(__file__).resolve().parents[2] / "game"))
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    marker = root / "modernization/assets/hd/HD_LAB.json"
    if not marker.is_file():
        raise SystemExit("Refusing to modify an unmarked game directory")
    lab = json.loads(marker.read_text(encoding="utf-8-sig"))
    if lab.get("kind") != "isolated-hd-game-lab" or Path(lab.get("root", "")).resolve() != root:
        raise SystemExit("HD lab marker does not match this directory")
    if digest((root / "Chaos.exe").read_bytes()) != SUPPORTED_EXE:
        raise SystemExit("Unknown executable hash")
    asset_path, pack_path, original_hash = ASSETS[args.asset]
    target = root / asset_path
    backup = root / "modernization/assets/hd/backups" / (args.asset + "-original.JPG")
    record = root / "modernization/assets/hd/backups" / (args.asset + "-trial.json")
    current_hash = digest(target.read_bytes())
    if args.mode == "status":
        print(json.dumps({"asset": args.asset, "sha256": current_hash, "original": current_hash == original_hash,
                          "backup_exists": backup.is_file(), "trial": json.loads(record.read_text()) if record.is_file() else None}, indent=2))
        return 0
    if args.mode == "restore":
        if not backup.is_file() or digest(backup.read_bytes()) != original_hash:
            raise SystemExit("Verified original backup is missing")
        if record.is_file():
            expected = json.loads(record.read_text())["installed_sha256"]
            if current_hash not in (original_hash, expected):
                raise SystemExit("Menu changed outside this trial; refusing restore")
        target.write_bytes(backup.read_bytes())
        print("Restored original", args.asset, digest(target.read_bytes()))
        return 0
    if current_hash != original_hash:
        raise SystemExit("Asset is already modified; restore it first")
    if backup.exists() and digest(backup.read_bytes()) != original_hash:
        raise SystemExit("Original backup hash mismatch")
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        backup.write_bytes(target.read_bytes())
    source = root / pack_path
    manifest_path = source.with_suffix(source.suffix + ".json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_sha256") != original_hash or manifest.get("output_sha256") != digest(source.read_bytes()):
        raise SystemExit("HD output manifest or source hash mismatch")
    with Image.open(source) as handle:
        if handle.format != "PNG" or handle.size != (1920, 1440):
            raise SystemExit("HD pack main menu has unexpected format or size")
        image = handle.convert("RGB")
    if args.mode == "install-800":
        image = image.resize((800, 600), Image.Resampling.LANCZOS)
    if args.mode == "install-png":
        data = source.read_bytes()
    else:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=100, subsampling=0)
        data = buffer.getvalue()
    state = {"status": "diagnostic-only-in-isolated-copy", "mode": args.mode,
             "asset": args.asset, "source_png": str(pack_path), "source_png_sha256": digest(source.read_bytes()),
             "original_sha256": original_hash, "installed_sha256": digest(data),
             "installed_size": list(image.size)}
    target.write_bytes(data)
    record.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print("Installed", args.mode, "in isolated copy:", state["installed_sha256"])
    print("Rollback: python modernization/tools/hd_menu_trial.py restore --asset", args.asset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
