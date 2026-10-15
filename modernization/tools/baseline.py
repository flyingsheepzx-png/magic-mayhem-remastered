"""Immutable baseline backup. Run before modifying the installed community build."""
from pathlib import Path
import hashlib
import json
import shutil
from datetime import datetime, timezone

ROOT = (Path(__file__).resolve().parents[2] / "game")
DEST = ROOT / "modernization" / "baseline"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest_path = DEST / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        broken = [name for name, meta in manifest["files"].items()
                  if not (DEST / name).is_file() or digest(DEST / name) != meta["sha256"]]
        if broken:
            raise SystemExit(f"Baseline damaged: {broken}")
        print(f"Existing baseline verified: {len(manifest['files'])} files")
        return
    files = [p for p in ROOT.iterdir() if p.is_file() and p.suffix.lower() in
             {".exe", ".dll", ".ini", ".cfg", ".enc", ".txt", ".wri"}]
    for folder in ("CFG", "Interface", "AI", "Save"):
        files.extend(p for p in (ROOT / folder).rglob("*") if p.is_file())
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "files": {}}
    for source in sorted(files):
        relative = source.relative_to(ROOT).as_posix()
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        manifest["files"][relative] = {"sha256": digest(target), "bytes": target.stat().st_size}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Baseline saved and hashed: {len(files)} files, {sum(m['bytes'] for m in manifest['files'].values())} bytes")

if __name__ == "__main__":
    main()
