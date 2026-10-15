"""Reversible background check of the ordinary mixed-render screenshot key."""
import ctypes
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import shutil
import time

from compare_hd_baseline import CaptureSession, ROOT, sha

def main():
    lab = ROOT / 'modernization/playtests/mixed-ui-v4'
    runtime = lab / 'game-wide169'
    wrapper, manifest = runtime / 'ddraw.dll', lab / 'manifest.json'
    fixture = runtime / 'Save/test2.sav'
    src = ROOT / 'modernization/backups/save-recovery/1790661735830701800/test2.sav'
    candidate = ROOT / 'modernization/build/cnc-ddraw-src/bin/Release/ddraw.dll'
    old_sha = '015a369ee8b8654434b3e745e61befe63346db521f4bb6acc5b3aca1e9e7796d'
    new_sha = '17ae19a205bdd21920b5eb66b2316fd7a6e76d9dcce0a9cccc027da747637b5f'
    fixture_sha = '56108a097a01f0bf7a9035d031d96a630e60c43be77808b9c567c65c33cba66d'
    if sha(wrapper) != old_sha or sha(candidate) != new_sha or sha(src) != fixture_sha or fixture.exists():
        raise RuntimeError('Unexpected package or fixture')
    old_wrapper, old_manifest = wrapper.read_bytes(), manifest.read_bytes()
    out = ROOT / 'modernization/assets/hd/battle-sharpen-trial' / str(time.time_ns())
    out.mkdir(parents=True)
    previous = os.environ.get('MM_PROBE_BATTLE_SHARPEN')
    try:
        fixture.write_bytes(src.read_bytes())
        wrapper.write_bytes(candidate.read_bytes())
        m = json.loads(old_manifest);m['files']['game-wide169/ddraw.dll'] = new_sha
        manifest.write_text(json.dumps(m, indent=2)+'\n', encoding='utf-8')
        os.environ['MM_PROBE_BATTLE_SHARPEN'] = '1'
        with CaptureSession('hd', out, 'mixed-ui-v4') as s:
            s.shot('private-menu')
            time.sleep(1.2)
            menu_before = set((runtime / 'ss').glob('*.png'))
            s.message(0x804f)
            time.sleep(1)
            menu_files = set((runtime / 'ss').glob('*.png')) - menu_before
            if len(menu_files) != 1:
                raise RuntimeError(f'Menu screenshot key produced {len(menu_files)} files')
            from PIL import Image, ImageChops
            with Image.open(menu_files.pop()) as a, Image.open(s.records['private-menu']['native']) as b:
                if a.size != (2560, 1440) or ImageChops.difference(a.convert('RGB'), b.convert('RGB')).getbbox():
                    raise RuntimeError('Menu screenshot key differs from presentation capture')
            s.load_fixture('test2', False)
            s.key(0x1b);time.sleep(.4)
            s.shot('private-escape')
            time.sleep(1.2)
            before = set((runtime / 'ss').glob('*.png'))
            s.message(0x804f)
            time.sleep(1)
            files = set((runtime / 'ss').glob('*.png')) - before
            if len(files) != 1:
                raise RuntimeError(f'Screenshot key produced {len(files)} files')
            dest = out / 'hotkey-escape.png';shutil.copy2(files.pop(), dest)
            with Image.open(dest) as a, Image.open(s.records['private-escape']['native']) as b:
                if a.size != (2560, 1440) or ImageChops.difference(a.convert('RGB'), b.convert('RGB')).getbbox():
                    raise RuntimeError('Screenshot key does not match the presentation capture')
            print('hotkey matches private presentation capture', dest, flush=True)
    finally:
        wrapper.write_bytes(old_wrapper);manifest.write_bytes(old_manifest)
        if fixture.exists() and sha(fixture) == fixture_sha:fixture.unlink()
        if previous is None:os.environ.pop('MM_PROBE_BATTLE_SHARPEN', None)
        else:os.environ['MM_PROBE_BATTLE_SHARPEN'] = previous

if __name__ == '__main__':main()
