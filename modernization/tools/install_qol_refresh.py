"""Build/install the v24 hotkey refresh fix, or restore the exact v23 entry."""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
from pathlib import Path
import shutil
import subprocess
import time

import pefile
from compare_hd_baseline import ROOT, baseline_identity, sha
from verify_hd60_runtime import configured_kernel, processes

BUILD = ROOT/'modernization/build/qol-refresh-v1'
PACKAGE = ROOT/'modernization/build/wide169/package-v24-qol-refresh'
ENTRY = ROOT/'game/Chaos-Wide169-Trial.exe'
BASE = ROOT/'modernization/current-baseline.json'
STATE = ROOT/'modernization/wide169-installed.json'
OLD = '8ef2806f8c383323f81cb2fb69fde2fdd30ebd208a32bdecbe363418caffa5c3'
ENGINE = '43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d'
QOL = 'ac2a3747bb92961c881f46b5f8d7b12fc361b254cd6421c311264b00ff20437c'

def write(path, data):
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')

def resources(path):
    pe = pefile.PE(str(path))
    return {(t.id, n.id, l.id): pe.get_data(l.data.struct.OffsetToData, l.data.struct.Size)
            for t in pe.DIRECTORY_ENTRY_RESOURCE.entries
            for n in t.directory.entries for l in n.directory.entries}

def idle():
    if any(n.startswith('chaos') for _, _, n in processes(configured_kernel())):
        raise RuntimeError('Close the game before installing')

def build():
    baseline_identity()
    assert sha(ENTRY) == OLD
    engine = ROOT/'game-wide169/Chaos-Wide169-engine.exe'
    assert sha(engine) == ENGINE
    pe = pefile.PE(str(engine))
    for address, expected in ((0x576d8b, 'e8504af6ff'), (0x46ede1, 'e8fac90600')):
        assert pe.get_data(address-0x400000, 5).hex() == expected
    BUILD.mkdir(parents=True, exist_ok=True)
    source = ROOT/'modernization/runtime/wide169/qol_bindings.cpp'
    shutil.copy2(source, BUILD/'qol_bindings.cpp')
    command = BUILD/'build.cmd'
    command.write_text('@echo off\ncall "C:\\Program Files\\Microsoft Visual Studio\\18\\Community\\VC\\Auxiliary\\Build\\vcvarsall.bat" x86 >nul\n'
                       'if errorlevel 1 exit /b 1\n'
                       'cl /nologo /LD /O2 /EHsc /std:c++17 /W4 qol_bindings.cpp /Foqol_bindings.obj /link /OUT:qol_bindings.dll user32.lib\n')
    subprocess.run(['cmd.exe', '/c', command.name], cwd=BUILD, check=True)
    candidate = BUILD/ENTRY.name
    shutil.copy2(ENTRY, candidate)
    original = resources(ENTRY)
    keys = [k for k in original if k[:2] == (10, 102)]
    assert len(keys) == 1
    import hashlib
    assert hashlib.sha256(original[keys[0]]).hexdigest() == QOL
    dll = (BUILD/'qol_bindings.dll').read_bytes()
    k = C.WinDLL('kernel32', use_last_error=True)
    k.BeginUpdateResourceW.argtypes = [W.LPCWSTR, W.BOOL]
    k.BeginUpdateResourceW.restype = W.HANDLE
    k.UpdateResourceW.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, W.WORD, C.c_void_p, W.DWORD]
    k.UpdateResourceW.restype = W.BOOL
    k.EndUpdateResourceW.argtypes = [W.HANDLE, W.BOOL]
    k.EndUpdateResourceW.restype = W.BOOL
    handle = k.BeginUpdateResourceW(str(candidate), False)
    if not handle: raise C.WinError(C.get_last_error())
    buffer = C.create_string_buffer(dll)
    if not k.UpdateResourceW(handle, 10, 102, keys[0][2], buffer, len(dll)):
        error = C.get_last_error(); k.EndUpdateResourceW(handle, True); raise C.WinError(error)
    if not k.EndUpdateResourceW(handle, False): raise C.WinError(C.get_last_error())
    expected = dict(original); expected[keys[0]] = dll
    assert resources(candidate) == expected
    a, b = pefile.PE(str(ENTRY)), pefile.PE(str(candidate))
    # The launcher code, terrain injection and all other embedded modules remain exact.
    for section in a.sections:
        if section.Name.rstrip(b'\0') != b'.rsrc':
            other = next(s for s in b.sections if s.Name == section.Name)
            assert section.get_data() == other.get_data()
    write(BUILD/'manifest.json', dict(parent_sha256=OLD, launcher_sha256=sha(candidate),
          qol_sha256=sha(BUILD/'qol_bindings.dll'), source_sha256=sha(source),
          engine_sha256=ENGINE, validation='Build and static integrity only; user performs gameplay testing'))

def install():
    idle(); baseline_identity()
    assert sha(ENTRY) == OLD and not PACKAGE.exists()
    report = json.loads((BUILD/'manifest.json').read_text())
    assert sha(BUILD/ENTRY.name) == report['launcher_sha256']
    state = json.loads(STATE.read_text()); parent = Path(state['package'])
    backup = ROOT/'modernization/backups/wide169'/('qol-refresh-'+str(time.time_ns()))
    backup.mkdir(parents=True)
    for p in (ENTRY, BASE, STATE): shutil.copy2(p, backup/p.name)
    protected = {p:sha(p) for folder in ('game-wide169/Save', 'game-wide169/CFG', 'modernization/config')
                 for p in (ROOT/folder).glob('*') if p.is_file()}
    protected[ROOT/'game-wide169/terrain_diagonal.dll'] = sha(ROOT/'game-wide169/terrain_diagonal.dll')
    protected[ROOT/'game-wide169/Chaos-Wide169-engine.exe'] = ENGINE
    shutil.copytree(parent/'runtime', PACKAGE/'runtime')
    shutil.copy2(BUILD/ENTRY.name, PACKAGE/ENTRY.name)
    spec = json.loads((parent/'manifest.json').read_text())
    spec.update(parent_package=str(parent), launcher_sha256=report['launcher_sha256'],
                qol_refresh=report, validation=report['validation'])
    write(PACKAGE/'manifest.json', spec)
    try:
        shutil.copy2(PACKAGE/ENTRY.name, ENTRY)
        assert sha(ENTRY) == report['launcher_sha256']
        state.update(package=str(PACKAGE), manifest_sha256=sha(PACKAGE/'manifest.json'),
                     qol_refresh_backup=str(backup))
        baseline = json.loads(BASE.read_text())
        baseline['latest_development']['files']['game/Chaos-Wide169-Trial.exe'] = sha(ENTRY)
        write(STATE, state); write(BASE, baseline)
        assert all(sha(p) == h for p, h in protected.items())
        baseline_identity()
    except BaseException:
        for p in (ENTRY, BASE, STATE): shutil.copy2(backup/p.name, p)
        raise
    write(backup/'installed.json', report)
    print(json.dumps(dict(status='installed', backup=str(backup), sha256=sha(ENTRY))))

def rollback():
    idle(); baseline_identity()
    state = json.loads(STATE.read_text()); assert state['package'] == str(PACKAGE)
    backup = Path(state['qol_refresh_backup'])
    report = json.loads((backup/'installed.json').read_text())
    assert sha(ENTRY) == report['launcher_sha256'] and sha(backup/ENTRY.name) == OLD
    for p in (ENTRY, BASE, STATE): shutil.copy2(backup/p.name, p)
    print('Restored the exact predecessor entry and manifests; saves/configuration untouched.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['build','install','rollback'])
    globals()[parser.parse_args().action]()
