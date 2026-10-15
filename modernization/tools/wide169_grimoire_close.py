"""Stage and install a hash-verified Wide169 Grimoire tab layout."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OLD_PACKAGE = ROOT / "modernization/build/wide169/package-v19-grimoire-tab-spacing"
NEW_PACKAGE = ROOT / "modernization/build/wide169/package-v20-grimoire-tab-clearance"
STATE = ROOT / "modernization/wide169-installed.json"
BASELINE = ROOT / "modernization/current-baseline.json"
CFG = Path("Interface/Grimoire/Grimoire.cfg")
OLD_CFG_SHA = "10a5b66e9a64dee252d170465d200dbae5e1f782b1c232b63f0c7163b541ccbf"
OLD_MANIFEST_SHA = "e9325db8e1d8d26a5570c4233f6fbc04d19724153f94392ead8cd6041046226e"
OLD_LAUNCHER_SHA = "84d201637ce3ccebf49b8c9f930c1e5d41083ecc40015d342e19e6ef9b232448"
OLD_ENGINE_SHA = "dbce6a86bfd9becefc3e680078b9f674c944cdb94352374484079c81fe4899dc"
BACKUP = ROOT / "modernization/backups/wide169/grimoire-tabs-v20"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(folder):
    result = {p.relative_to(folder).as_posix(): sha(p)
            for p in folder.rglob("*") if p.is_file()
            and not any(part in ("modernization", "ss") for part in p.relative_to(folder).parts)}
    config = folder / "modernization/config/qol-hotkeys.json"
    if config.is_file():
        result["modernization/config/qol-hotkeys.json"] = sha(config)
    return result


def verify_base():
    state = json.loads(STATE.read_text())
    baseline = json.loads(BASELINE.read_text())["latest_development"]
    assert Path(state["package"]).resolve() == OLD_PACKAGE.resolve()
    assert state["manifest_sha256"] == sha(OLD_PACKAGE / "manifest.json") == OLD_MANIFEST_SHA
    assert baseline["files"]["game/Chaos-Wide169-Trial.exe"] == OLD_LAUNCHER_SHA
    assert baseline["files"]["game-wide169/Chaos-Wide169-engine.exe"] == OLD_ENGINE_SHA
    assert sha(ROOT / "game/Chaos-Wide169-Trial.exe") == OLD_LAUNCHER_SHA
    assert sha(ROOT / "game-wide169/Chaos-Wide169-engine.exe") == OLD_ENGINE_SHA
    old = json.loads((OLD_PACKAGE / "manifest.json").read_text())
    assert old["launcher_sha256"] == OLD_LAUNCHER_SHA and old["engine_sha256"] == OLD_ENGINE_SHA
    assert sha(OLD_PACKAGE / "runtime" / CFG) == sha(ROOT / "game-wide169" / CFG) == OLD_CFG_SHA
    return state, old


def patch_bytes(data):
    assert hashlib.sha256(data).hexdigest() == OLD_CFG_SHA
    old_ys = (78, 146, 214, 478, 546, 614)
    new_ys = (80, 152, 219, 477, 544, 611)
    for index, old_y, new_y in zip((2, 3, 4, 6, 7, 8), old_ys, new_ys):
        before = f"800x600_{index}RY = {old_y}".encode()
        after = f"800x600_{index}RY = {new_y}".encode()
        assert data.count(before) == 1
        data = data.replace(before, after)
    return data


def build():
    state, old = verify_base()
    if NEW_PACKAGE.exists():
        raise RuntimeError("Candidate package exists")
    shutil.copytree(OLD_PACKAGE / "runtime", NEW_PACKAGE / "runtime")
    shutil.copy2(OLD_PACKAGE / "Chaos-Wide169-Trial.exe", NEW_PACKAGE / "Chaos-Wide169-Trial.exe")
    path = NEW_PACKAGE / "runtime" / CFG
    path.write_bytes(patch_bytes(path.read_bytes()))
    spec = dict(old)
    spec["parent_package"] = str(OLD_PACKAGE)
    spec["files"] = dict(old["files"])
    spec["files"][CFG.as_posix()] = sha(path)
    spec["grimoire_tabs"] = "Keep right tabs at X=1026; distribute four above and four below the book clasp (Y=286-403), with adjacent hit rectangles touching but not overlapping."
    assert inventory(NEW_PACKAGE / "runtime") == spec["files"]
    (NEW_PACKAGE / "manifest.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"package": str(NEW_PACKAGE), "files": len(spec["files"]),
                      "manifest_sha256": sha(NEW_PACKAGE / "manifest.json"),
                      "config_sha256": sha(path)}, indent=2))


def install():
    state, old = verify_base()
    spec = json.loads((NEW_PACKAGE / "manifest.json").read_text())
    assert len(spec["files"]) == len(old["files"])
    assert inventory(NEW_PACKAGE / "runtime") == spec["files"]
    assert sha(NEW_PACKAGE / "Chaos-Wide169-Trial.exe") == OLD_LAUNCHER_SHA
    dest = ROOT / "game-wide169" / CFG
    if BACKUP.exists():
        raise RuntimeError("Backup exists")
    BACKUP.mkdir(parents=True)
    shutil.copy2(dest, BACKUP / CFG.name)
    shutil.copy2(STATE, BACKUP / STATE.name)
    shutil.copy2(NEW_PACKAGE / "runtime" / CFG, dest)
    assert sha(dest) == spec["files"][CFG.as_posix()]
    state.update(package=str(NEW_PACKAGE), manifest_sha256=sha(NEW_PACKAGE / "manifest.json"),
                 grimoire_close_backup=str(BACKUP))
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"installed": str(dest), "backup": str(BACKUP),
                      "config_sha256": sha(dest)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "install"))
    globals()[parser.parse_args().action]()
