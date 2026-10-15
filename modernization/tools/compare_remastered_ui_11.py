"""Bounded, opt-in Remastered 1.0/1.1 UI comparison; no launch without --run.

Reuses compare_hd_baseline.CaptureSession for surface capture and telemetry.
Only private background input and read-only process memory are used. Both
packages are copied to fresh workspaces; installed saves/config are never edited.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes as W
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'modernization/releases/remastered-1.0/runtime'
CANDIDATE = ROOT / 'modernization/playtests/remastered-1.1-p1'
BASE_MANIFEST = '6035baf0d590cf1e4bf0a5ad588edb739bb8ee29eb668b6f27f23886012f2b43'
CANDIDATE_MANIFEST = '0a66f2e073b905b23a869a3ea0041e32c7691781a7331d02c33b628d2c9f3d07'
ENGINES = {
    '1.0': '43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d',
    '1.1': '42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da',
}
DIAGNOSTIC = ROOT / 'modernization/assets/hd/background-noactivate-ddraw.dll'
DIAGNOSTIC_SHA = '217ada6704b3eaf7d0ca1efde41980a303d2c8ad72925fcd50e285f8072dfec8'
SCREENS = ('menu', 'new-game-map', 'region-hover', 'grimoire', 'return-initial-focus')
REALM_SCREENS = ('menu','load','realm-loaded','region-hover','grimoire','return-initial-focus')
PORT_SCREENS=('menu','load','realm-loaded','portmanteau','portmanteau-talisman-hover','portmanteau-middle-hover')
PORT_FULL_SCREENS=PORT_SCREENS+('portmanteau-chaos-hover','portmanteau-law-selected','portmanteau-neutral-selected','portmanteau-chaos-selected','grimoire','portmanteau-return')
CORE_SCREENS = ('menu','options','load','battle','escape','save','battle-return')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def guarded_path(root, name):
    p = (root / name).resolve()
    if not p.is_relative_to(root.resolve()):
        raise RuntimeError('Manifest path escapes package: ' + name)
    return p


def files(root):
    """Reject junctions/symlinks instead of following runtime aliases."""
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            p = Path(directory) / name
            if p.is_symlink() or (getattr(p.stat(), 'st_file_attributes', 0) & 0x400):
                raise RuntimeError('Reparse point in package: ' + str(p))
        for name in names:
            yield Path(directory) / name


def mutable_name(name):
    n = name.replace('\\', '/').lower()
    return (n.startswith(('save/', 'cfg/', 'ai/', 'modernization/config/'))
            or ('/' not in n and n.endswith(('.cfg', '.ini'))) or n in ('ddraw.dll','fmv-h264-events.jsonl'))


def user_state_name(name):
    # Keep static CFG definitions hash-gated, matching build_remastered_11.verify.
    n = name.replace('\\', '/').lower()
    return (n.startswith(('save/', 'cfg/encrypted/', 'ss/', 'logs/', 'modernization/logs/'))
            or n in ('cfg/prefs.cfg', 'ddraw.ini', 'ai/experien.dat', 'ai/brain.dat',
                     'modernization/config/qol-hotkeys.json','fmv-h264-events.jsonl'))


def verify_package(package, version, manifest_sha):
    package = package.resolve()
    manifest = package / ('release-manifest.json' if version == '1.0' else 'manifest.json')
    if sha(manifest) != manifest_sha:
        raise RuntimeError(f'{version} manifest changed; review it and supply its exact SHA-256')
    m = json.loads(manifest.read_text(encoding='utf-8'))
    if m['version'] != version or m['engine_sha256'] != ENGINES[version]:
        raise RuntimeError('Unknown address-map engine/version: ' + version)
    launcher = package / ('MagicMayhem-Remastered.exe' if version == '1.0'
                          else 'MagicMayhem-Remastered-1.1.exe')
    if sha(launcher) != m['launcher_sha256']:
        raise RuntimeError('Launcher identity mismatch: ' + str(launcher))
    for name, digest in m['files'].items():
        p = guarded_path(package if version == '1.0' else package / 'runtime', name)
        relative = p.relative_to(package / 'runtime').as_posix() if p.is_relative_to(package / 'runtime') else name
        # Player state may differ from the packaging snapshot. Hash/report it
        # independently; never bypass engine, wrapper or static asset guards.
        user_state = user_state_name(relative)
        if not user_state and sha(p) != digest:
            raise RuntimeError('Package identity mismatch: ' + str(p))
    # Include unlisted files in the source audit; refuse unmanifested code/assets.
    runtime = package / 'runtime'
    listed = set(m['files'])
    for p in files(runtime):
        rel = p.relative_to(runtime).as_posix()
        key = 'runtime/' + rel if version == '1.0' else rel
        if key not in listed and not (user_state_name(rel) or rel.lower().startswith(('ss/', 'logs/', 'modernization/logs/'))):
            raise RuntimeError('Unmanifested runtime file: ' + str(p))
    if sha(runtime / 'Chaos-Wide169-engine.exe') != ENGINES[version]:
        raise RuntimeError('Engine file identity mismatch')
    if version == '1.1' and any(m.get(k) != v for k, v in {
        'native_ui': [1920, 1440], 'ui_origin': [320, 0], 'native_battle': [1280, 720],
        'output': [2560, 1440], 'logic_preference': 30, 'filter': 'disabled',
    }.items()):
        raise RuntimeError('Unknown mixed rendering contract')
    mutable_hashes = {p.relative_to(runtime).as_posix(): sha(p) for p in files(runtime)
                      if mutable_name(p.relative_to(runtime).as_posix())
                      and p.name.lower() != 'ddraw.dll'}
    return dict(version=version, package=str(package), manifest_sha256=manifest_sha,
                mutable_hashes=mutable_hashes,
                launcher_sha256=sha(launcher), engine_sha256=ENGINES[version],
                launcher_name=launcher.name)


def stage(identity, destination, fixture=None):
    source = Path(identity['package'])
    destination.mkdir(parents=True, exist_ok=False)
    # Keep the launcher's sibling runtime layout; never hardlink mutable files.
    shutil.copy2(source / identity['launcher_name'], destination / identity['launcher_name'])
    runtime = destination / 'runtime'
    runtime.mkdir()
    for p in files(source / 'runtime'):
        rel = p.relative_to(source / 'runtime')
        if rel.parts[0].lower() in ('ss', 'logs') or rel.as_posix().lower().startswith('modernization/logs/'):
            continue
        target = runtime / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        if sha(target) != sha(p):
            raise RuntimeError('Copy verification failed: ' + str(p))
    if fixture:
        # The same bytes/timestamp in both copies; preserve original saves.
        target = runtime / 'Save' / fixture.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and sha(target) != sha(fixture):
            raise RuntimeError('Fixture name conflicts with an existing save')
        shutil.copy2(fixture, target)
        stamp=time.time_ns();os.utime(target,ns=(stamp,stamp))  # visible first load row in both labs
    return runtime


# Heavy Win32/PE dependencies load only after argument parsing: --help is inert.
def session_class():
    import wide169_trial
    from compare_hd_baseline import CaptureSession

    class RemasteredSession(CaptureSession):
        """Package-specific startup/cleanup; inherited UI methods remain reusable."""
        def __init__(self, identity, runtime, output, seconds):
            # Session.__init__ would create an unrelated log folder. Initialize
            # its declared Win32 API contract here without launching anything.
            self.k = wide169_trial.configured_kernel()
            self.u = ctypes.WinDLL('user32', use_last_error=True)
            self.u.GetWindowThreadProcessId.argtypes = [W.HWND, ctypes.POINTER(W.DWORD)]
            self.u.GetClientRect.argtypes = [W.HWND, ctypes.POINTER(W.RECT)]
            self.u.GetClientRect.restype = W.BOOL
            self.u.RegisterWindowMessageW.argtypes = [W.LPCWSTR]
            self.u.RegisterWindowMessageW.restype = W.UINT
            self.u.SendMessageTimeoutW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM,
                                                  W.UINT, W.UINT, ctypes.POINTER(ctypes.c_size_t)]
            self.u.SendMessageTimeoutW.restype = ctypes.c_size_t
            self.cb = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
            self.u.EnumWindows.argtypes = [self.cb, W.LPARAM]
            self.u.EnumWindows.restype = W.BOOL
            self.u.IsWindowVisible.argtypes = [W.HWND]
            self.u.IsWindowVisible.restype = W.BOOL
            self.k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR,
                                                          ctypes.POINTER(W.DWORD)]
            self.k.QueryFullProcessImageNameW.restype = W.BOOL
            self.k.GetExitCodeProcess.argtypes = [W.HANDLE, ctypes.POINTER(W.DWORD)]
            self.k.GetExitCodeProcess.restype = W.BOOL
            self.k.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
            self.k.WaitForSingleObject.restype = W.DWORD
            self.identity = identity
            self.label = identity['version']
            self.hd = self.label == '1.1'
            self.factor = 2 if self.hd else 1
            self.lab = runtime
            self.entry = runtime.parent / identity['launcher_name']
            self.engine = runtime / 'Chaos-Wide169-engine.exe'
            self.run = output
            self.run.mkdir()
            self.result = dict(identity=identity, checks={}, screenshots={}, actions=[])
            self.records = {}
            self.proc = self.handle = self.stop_handle = None
            self.mutable = {}
            self.seconds = seconds
            self.finished = threading.Event()
            self.timed_out = threading.Event()
            self.watchdog = None
            self.old_lab = wide169_trial.LAB
            self.before_saves = set()

        def path_for_handle(self, handle):
            size = W.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not self.k.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                raise ctypes.WinError(ctypes.get_last_error())
            return Path(buffer.value).resolve()

        def check_deadline(self):
            if self.timed_out.is_set() or time.monotonic() >= self.deadline:
                raise TimeoutError('Session time limit reached')
            if self.handle:
                code = W.DWORD()
                if not self.k.GetExitCodeProcess(self.handle, ctypes.byref(code)):
                    raise ctypes.WinError(ctypes.get_last_error())
                if code.value != 259:
                    raise RuntimeError('Owned engine exited')

        def stop_owned(self):
            # A child may appear at the startup deadline or while start() raises.
            # Discover only children of our Popen PID, with the exact engine name.
            if self.proc and not self.stop_handle:
                ids = [pid for pid, parent, name in wide169_trial.processes(self.k)
                       if parent == self.proc.pid and name == self.engine.name.lower()]
                if len(ids) > 1:
                    raise RuntimeError('Ambiguous engine ownership during cleanup')
                if ids:
                    self.stop_handle = self.k.OpenProcess(0x101001, False, ids[0])
                    if not self.stop_handle:
                        raise ctypes.WinError(ctypes.get_last_error())
            # Handle identity cannot be recycled to a different PID/process.
            if self.stop_handle:
                if self.k.WaitForSingleObject(self.stop_handle, 0) == 258:
                    if self.path_for_handle(self.stop_handle) != self.engine.resolve():
                        raise RuntimeError('Cleanup engine ownership mismatch')
                    if not self.k.TerminateProcess(self.stop_handle, 0):
                        raise ctypes.WinError(ctypes.get_last_error())
                    if self.k.WaitForSingleObject(self.stop_handle, 5000) != 0:
                        raise RuntimeError('Owned engine did not stop')
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
                self.proc.wait(timeout=5)

        def start(self):
            if any(name.startswith(('chaos', 'magicmayhem'))
                   for _, _, name in wide169_trial.processes(self.k)):
                raise RuntimeError('A game is running; close it before comparing')
            if sha(self.engine) != self.identity['engine_sha256'] or sha(self.entry) != self.identity['launcher_sha256']:
                raise RuntimeError('Staged executable identity changed')
            for p in files(self.lab):
                if mutable_name(p.relative_to(self.lab).as_posix()):
                    st = p.stat()
                    backup = self.run / 'mutable-backup' / p.relative_to(self.lab)
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, backup)
                    self.mutable[p] = (backup, sha(p), st.st_atime_ns, st.st_mtime_ns)
            self.before_saves = set((self.lab / 'Save').glob('*'))
            write_json(self.run / 'backup.json', {str(p.relative_to(self.lab)): {
                'sha256': row[1], 'atime_ns': row[2], 'mtime_ns': row[3]
            } for p, row in self.mutable.items()})
            # Explicit FMV skip in disposable prefs only, after disk backup.
            prefs = self.lab / 'CFG/prefs.cfg'
            data = prefs.read_bytes()
            for setting in (b'PlayFMV', b'PlayFMVOut'):
                pattern = rb'(?m)^(' + setting + rb'\s*=\s*)[^\r\n]*'
                value=b'TRUE' if setting==b'PlayFMV' and getattr(self,'startup_fmv',False) else b'FALSE'
                data, count = re.subn(pattern, rb'\g<1>'+value, data)
                if count != 1:
                    raise RuntimeError('Missing/ambiguous FMV preference: ' + setting.decode())
            expected_logic=getattr(self,'expected_logic',30)
            if expected_logic not in (20,30,40):raise ValueError('Unknown options logic test rate')
            if not re.search(rb'(?m)^MaxFramesPerSec\s*=\s*'+str(expected_logic).encode()+rb'\s*$', data):
                raise RuntimeError('Unexpected logic preference for this isolated test')
            prefs.write_bytes(data)
            self.result['fmv_policy'] = ('PlayFMV=TRUE, owned startup callback skips actual movie; PlayFMVOut=FALSE; restored finally' if getattr(self,'startup_fmv',False) else 'PlayFMV=FALSE and PlayFMVOut=FALSE in isolated prefs; restored finally')
            env = {k: v for k, v in os.environ.items() if not k.upper().startswith('MM_PROBE_')}
            env['MM_PROBE_BACKGROUND_INPUT'] = '1'
            diagnostic_environment=getattr(self,'diagnostic_environment',{})
            if any(not key.startswith('MM_PROBE_') for key in diagnostic_environment):
                raise ValueError('Diagnostic environment must use MM_PROBE_ keys')
            env.update(diagnostic_environment)
            if self.hd:
                env.update(MM_PROBE_MIXED_RENDER='1', MM_PROBE_MIXED_FONTS='1',
                           MM_PROBE_BATTLE_SHARPEN='0')
            else:
                if sha(DIAGNOSTIC) != DIAGNOSTIC_SHA:
                    raise RuntimeError('Unknown baseline diagnostic wrapper')
                shutil.copy2(DIAGNOSTIC, self.lab / 'ddraw.dll')
            self.result['environment'] = {k: v for k, v in env.items() if k.startswith('MM_PROBE_')}
            wide169_trial.LAB = self.lab  # inherited capture() uses this global
            self.deadline = time.monotonic() + self.seconds
            self.proc = subprocess.Popen([str(self.entry), *getattr(self, 'launcher_args', [])], cwd=self.lab, env=env)
            self.result['launcher_pid'] = self.proc.pid
            startup_deadline = min(self.deadline, time.monotonic() + 20)
            while time.monotonic() < startup_deadline:
                ids = [pid for pid, parent, name in wide169_trial.processes(self.k)
                       if parent == self.proc.pid and name == self.engine.name.lower()]
                if len(ids) > 1:
                    raise RuntimeError('Ambiguous engine ownership')
                if ids:
                    self.pid = ids[0]
                    # Obtain cleanup ownership before observation/verification.
                    self.stop_handle = self.k.OpenProcess(0x100001 | 0x1000, False, self.pid)
                    if not self.stop_handle:
                        raise ctypes.WinError(ctypes.get_last_error())
                    if self.path_for_handle(self.stop_handle) != self.engine.resolve():
                        raise RuntimeError('Unexpected engine process path')
                    self.handle = self.k.OpenProcess(0x1010, False, self.pid)
                    if not self.handle:
                        raise ctypes.WinError(ctypes.get_last_error())
                    if sha(self.path_for_handle(self.handle)) != self.identity['engine_sha256']:
                        raise RuntimeError('Running engine identity mismatch')
                    break
                if self.proc.poll() is not None:
                    raise RuntimeError('Launcher exited before engine discovery')
                time.sleep(.1)
            else:
                raise TimeoutError('Owned engine missing at startup deadline')
            self.result['engine_pid'] = self.pid
            def watch():
                if not self.finished.wait(max(0, self.deadline - time.monotonic())):
                    self.timed_out.set()
                    try:
                        self.stop_owned()
                    except BaseException as e:
                        self.result['watchdog_error'] = str(e)
            self.watchdog = threading.Thread(target=watch, daemon=True)
            self.watchdog.start()
            self.channel = self.u.RegisterWindowMessageW('MagicMayhem.Probe.BackgroundMouse.v1')
            if not self.channel:
                raise ctypes.WinError(ctypes.get_last_error())
            # Startup covers child discovery, window/handshake and menu gate.
            # Retry only readiness while bounded; never fall back to foreground.
            last_error = None
            while time.monotonic() < startup_deadline:
                try:
                    startup_action=getattr(self,'startup_ui_action',None)
                    if startup_action:startup_action()
                    self.message(0)
                    surface = [self.i(0x6a49f0), self.i(0x6a49f4)]
                    controls = self.controls()
                    # Main-menu New Game control contains the known hit point.
                    x, y = 640 * self.factor, 396 * self.factor
                    if surface == ([2560, 1440] if self.hd else [1280, 720]) and any(
                        c['rect'][0] <= x < c['rect'][2] and c['rect'][1] <= y < c['rect'][3]
                        for c in controls):
                        break
                    last_error = 'Menu/surface not ready'
                except (RuntimeError, OSError) as e:
                    last_error = str(e)
                time.sleep(.1)
            else:
                raise TimeoutError('Startup/menu deadline (20s): ' + str(last_error))
            self.result['startup_seconds'] = self.seconds - (self.deadline - time.monotonic())
            surface = [self.i(0x6a49f0), self.i(0x6a49f4)]
            if surface != ([2560, 1440] if self.hd else [1280, 720]) or self.i(0x6de6fd) != expected_logic:
                raise RuntimeError('Unexpected primary geometry/frame preference')
            rect = W.RECT()
            if not self.u.GetClientRect(self.window(), ctypes.byref(rect)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.result['surface'] = surface
            self.result['physical_client'] = [rect.right, rect.bottom]
            # Private protocol accepts primary/presentation coordinates, not
            # client pixels. A bordered window may be fitted to the desktop.
            # Preserve native surfaces at full size; never infer geometry from
            # a physical client or silently label a scaled client native output.
            if rect.right <= 0 or rect.bottom <= 0:
                raise RuntimeError('Invalid physical client geometry')
            self.result['client_scale'] = [rect.right / 2560, rect.bottom / 1440]
            self.result['output_capture_contract'] = ('native 2560x1440 game surface' if self.hd
                else 'native 1280x720 surface reconstructed exactly 2x for paired comparison')
            return self

        def message(self, event, x=0, y=0):
            self.check_deadline()
            width, height = (2560, 1440) if self.hd else (1280, 720)
            if not 0 <= x < width or not 0 <= y < height:
                raise ValueError('Private surface coordinate outside verified bounds')
            return super().message(event, x, y)

        def i(self, address):
            self.check_deadline()
            return super().i(address)

        def shot(self, name, move_cursor=True):
            self.check_deadline()
            for attempt in range(4):
                super().shot(name, move_cursor)
                try:self.require_visible(name);break
                except RuntimeError:
                    transient=self.run/'transient';transient.mkdir(exist_ok=True)
                    for key in ('native','output'):
                        source=Path(self.records[name][key]);shutil.copy2(source,transient/(source.stem+'-attempt'+str(attempt)+source.suffix))
                    self.result.setdefault('transient_captures',[]).append(dict(name=name,attempt=attempt,lit_fraction=self.records[name].get('lit_fraction')))
                    if attempt==3:raise
                    time.sleep(.5)
            self.records[name]['region_id'] = self.i(0x659f51)
            self.records[name]['monotonic'] = time.monotonic()

        def __exit__(self, typ, error, tb):
            self.finished.set()
            if self.watchdog:
                self.watchdog.join(timeout=11)
            failures = []
            try:
                self.stop_owned()
            except BaseException as e:
                failures.append('owned process cleanup: ' + str(e))
            # Never restore files while the engine might still be writing them.
            stopped = (not self.stop_handle or self.k.WaitForSingleObject(self.stop_handle, 0) == 0) and (not self.proc or self.proc.poll() is not None)
            if stopped:
                for p, (backup, digest, atime, mtime) in self.mutable.items():
                    try:
                        p.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup, p)
                        os.utime(p, ns=(atime, mtime))
                        if sha(p) != digest:
                            raise RuntimeError('Restored bytes differ')
                    except BaseException as e:
                        failures.append(str(p) + ': ' + str(e))
                for p in (self.lab / 'Save').glob('*'):
                    if p.is_file() and p not in self.before_saves:
                        target = self.run / 'new-saves' / p.name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            shutil.copy2(p, target)  # retain both; never delete unfamiliar saves
                        except BaseException as e:
                            failures.append('New save archive: ' + str(e))
            else:
                failures.append('Restoration deferred because engine exit was not confirmed')
            for handle in (self.handle, self.stop_handle):
                if handle:
                    self.k.CloseHandle(handle)
            self.handle = self.stop_handle = None
            wide169_trial.LAB = self.old_lab
            self.result.update(screens=self.records, cleanup_errors=failures,
                               timed_out=self.timed_out.is_set(), restored=not failures,
                               status='failed' if error or failures or self.timed_out.is_set() else 'captured')
            if error:
                self.result['error'] = str(error)
            write_json(self.run / 'capture.json', self.result)
            if failures:
                raise RuntimeError('Cleanup failed; retain backups: ' + '; '.join(failures)) from error

    return RemasteredSession


def wait_control(session, predicate, seconds=10):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        session.check_deadline()
        controls=[c for c in session.controls() if predicate(c)]
        if controls:return controls
        time.sleep(.1)
    raise TimeoutError('Expected UI control did not arrive')


def capture_core_flow(session,fixture):
    with session as s:
        target=s.lab/'Save'/fixture.name;stamp=time.time_ns();os.utime(target,ns=(stamp,stamp))
        s.shot('menu');s.click_base(640,576)
        wait_control(s,lambda c:c['vtable']=='0x5c6c6c' and c['rect']==[x*s.factor for x in (796,636,1072,684)])
        s.shot('options');s.click_base(938,666)
        wait_control(s,lambda c:c['vtable']=='0x5c6c6c' and c['rect']==[x*s.factor for x in (340,432,940,480)])
        s.load_fixture(fixture.stem)
        wait_control(s,lambda c:c['vtable']=='0x5c6f54');s.shot('battle')
        if s.records['battle']['font_heights']!=[32,22,15]:raise RuntimeError('Battle font scale changed')
        scanner=wait_control(s,lambda c:c['vtable']=='0x5c6a8c')
        if len(scanner)!=1 or scanner[0]['rect']!=[1112,6,1272,86]:raise RuntimeError('Scanner is outside native battle viewport: '+str(scanner))
        camera=[]
        for x,y in [(1222,46),(1162,46)]:
            before=[s.i(0x689969),s.i(0x68996d)]
            for event in (0x200,0x201,0x202):s.message(event,x*s.factor,y*s.factor);time.sleep(.09)
            time.sleep(.25);after=[s.i(0x689969),s.i(0x68996d)]
            if before==after:raise RuntimeError('Scanner click did not move camera')
            camera.append(dict(native_click=[x,y],before=before,after=after))
        s.result['checks']['minimap']=dict(rect=scanner[0]['rect'],camera_clicks=camera)
        s.key(0x1b);time.sleep(.6)
        wait_control(s,lambda c:c['rect']==[460,276,820,324]);s.shot('escape')
        s.click_base(640,300)
        wait_control(s,lambda c:c['vtable']=='0x5c6db8');s.shot('save')
        if s.hd and s.records['save']['font_heights']!=[64,44,30]:raise RuntimeError('Save UI did not restore native UI fonts')
        s.click_base(938,666);time.sleep(.5)
        if any(c['rect']==[460,456,820,504] for c in s.controls()):s.click_base(640,480)
        time.sleep(.6);s.shot('battle-return')
        if s.records['battle-return']['font_heights']!=[32,22,15]:raise RuntimeError('Return doubled battle fonts')
        s.result['checks']['mixed_ui_battle_transitions']='passed'
    return s.records


def capture_port_flow(session,fixture,full=False):
    with session as s:
        target=s.lab/'Save'/fixture.name;stamp=time.time_ns();os.utime(target,ns=(stamp,stamp))
        s.shot('menu');s.load_fixture(fixture.stem)
        def toolbar(c):
            r=c['rect'];return c['vtable']=='0x5c6bd0' and 0<=r[1]<100*s.factor and 850*s.factor<r[0] and r[2]<=1120*s.factor
        buttons=sorted(wait_control(s,toolbar),key=lambda c:c['rect'][0])
        if len(buttons)!=4:raise RuntimeError('Expected four campaign buttons')
        s.shot('realm-loaded')
        rect=buttons[-1]['rect'];s.result['actions'].append(dict(action='open-portmanteau',control_rect=rect))
        x,y=(rect[0]+rect[2])//2,(rect[1]+rect[3])//2
        for e in (0x200,0x201,0x202):s.message(e,x,y);time.sleep(.09)
        wait_control(s,lambda c:c['vtable']=='0x5c77f0')
        for _ in range(4):s.click_base(640,360);time.sleep(.25)
        s.shot('portmanteau')
        talisman=sorted([c['rect'] for c in s.controls() if c['vtable']=='0x5c77bc' and c['rect'][1]>=600*s.factor],key=lambda r:r[0])
        if len(talisman)!=3:raise RuntimeError('Expected three talisman controls: '+str(talisman))
        s.result['checks']['talisman_controls']=talisman
        for name,r in zip(('portmanteau-talisman-hover','portmanteau-middle-hover'),talisman[:2]):
            s.message(0x200,(r[0]+r[2])//2,(r[1]+r[3])//2);time.sleep(1)
            s.shot(name,move_cursor=False)
            s.result['actions'].append(dict(action='hover-talisman',control_rect=r))
        if full:
            r=talisman[2];s.message(0x200,(r[0]+r[2])//2,(r[1]+r[3])//2);time.sleep(1);s.shot('portmanteau-chaos-hover',move_cursor=False)
            for name,r in zip(('portmanteau-law-selected','portmanteau-neutral-selected','portmanteau-chaos-selected'),talisman):
                x,y=(r[0]+r[2])//2,(r[1]+r[3])//2
                for e in (0x200,0x201,0x202):s.message(e,x,y);time.sleep(.09)
                time.sleep(.4);s.shot(name)
                if not any(c['vtable']=='0x5c77f0' for c in s.controls()):raise RuntimeError('Selecting talisman closed Portmanteau')
            top=sorted([c['rect'] for c in s.controls() if c['vtable']=='0x5c7780' and c['rect'][1]<100*s.factor and c['rect'][0]>850*s.factor],key=lambda r:r[0])
            if len(top)!=3:raise RuntimeError('Portmanteau navigation buttons absent')
            r=top[1];x,y=(r[0]+r[2])//2,(r[1]+r[3])//2
            for e in (0x200,0x201,0x202):s.message(e,x,y);time.sleep(.09)
            close=wait_control(s,lambda c:c['vtable']=='0x5c6bd0' and c['rect'][:2]==[1088*s.factor,286*s.factor])
            s.shot('grimoire');r=close[0]['rect'];x,y=(r[0]+r[2])//2,(r[1]+r[3])//2
            for e in (0x200,0x201,0x202):s.message(e,x,y);time.sleep(.09)
            wait_control(s,lambda c:c['vtable']=='0x5c77f0');s.shot('portmanteau-return')
            s.result['checks']['talisman_click_and_grimoire_roundtrip']='passed'
        s.result['checks']['portmanteau_arrived']=True
    return s.records


def capture_port_full_flow(session,fixture):return capture_port_flow(session,fixture,True)


def verify_minimap_pixels(records):
    # Geometry/camera telemetry alone missed the per-frame draw-origin bug.
    # Compare the interior diamond, excluding its surrounding animated scene.
    import numpy as np
    from PIL import Image
    crops=[np.array(Image.open(records[v]['battle']['output']).convert('RGB').crop((2200,0,2560,200))) for v in ('1.0','1.1')]
    y,x=np.mgrid[:200,:360]
    mask=(np.abs(x-184)/142+np.abs(y-92)/68)<.92
    fraction=float(np.all(crops[0]==crops[1],axis=2)[mask].mean())
    if fraction<.85:raise RuntimeError('Minimap pixels differ/missing despite valid controls: '+str(fraction))
    return dict(interior_pixels=int(mask.sum()),exact_match_fraction=fraction,minimum=.85)


def capture_realm_flow(session,fixture):
    with session as s:
        target=s.lab/'Save'/fixture.name;stamp=time.time_ns();os.utime(target,ns=(stamp,stamp))
        s.shot('menu')
        s.load_fixture(fixture.stem)
        s.result['actions'].append({'action':'load-identical-fixture','name':fixture.name,'sha256':sha(fixture)})
        def toolbar(c):
            r=c['rect'];return c['vtable']=='0x5c6bd0' and 0<=r[1]<100*s.factor and 850*s.factor<r[0] and r[2]<=1120*s.factor
        buttons=wait_control(s,toolbar)
        if len(buttons)!=4:raise RuntimeError('Expected four campaign toolbar controls: '+str([c['rect'] for c in buttons]))
        buttons=sorted(buttons,key=lambda c:c['rect'][0])
        s.result['toolbar_rects']=[c['rect'] for c in buttons]
        s.shot('realm-loaded');initial=s.i(0x659f51);s.result['initial_region_id']=initial
        s.message(0x200,760*s.factor,224*s.factor);time.sleep(1)
        s.shot('region-hover',move_cursor=False)
        if s.i(0x659f51)!=initial:raise RuntimeError('Hover altered campaign focus')
        rect=buttons[2]['rect'];x=(rect[0]+rect[2])//2;y=(rect[1]+rect[3])//2
        s.result['actions'].append({'action':'open-grimoire','actual_control_rect':rect})
        for e in (0x200,0x201,0x202):s.message(e,x,y);time.sleep(.09)
        close=wait_control(s,lambda c:c['vtable']=='0x5c6bd0' and c['rect'][:2]==[1088*s.factor,286*s.factor])
        if len(close)!=1:raise RuntimeError('Ambiguous Grimoire close control')
        s.shot('grimoire')
        rect=close[0]['rect'];x=(rect[0]+rect[2])//2;y=(rect[1]+rect[3])//2
        for e in (0x200,0x201,0x202):s.message(e,x,y);time.sleep(.09)
        wait_control(s,toolbar);s.shot('return-initial-focus')
        if s.i(0x659f51)!=initial:raise RuntimeError('Grimoire return changed campaign focus')
    return s.records


def capture_flow(session):
    with session as s:
        s.shot('menu')
        s.result['actions'].append({'action': 'new-game', 'base_coordinate': [640, 396]})
        s.click_base(640, 396)
        wait_control(s, lambda c:c['rect']==[x*s.factor for x in (940,30,1012,102)])
        initial = s.i(0x659f51)
        s.shot('new-game-map')
        s.result['new_game_saves'] = {p.name: sha(p) for p in (s.lab / 'Save').glob('*.sav')}
        s.result['initial_region_id'] = initial
        s.result['actions'].append({'action': 'hover-only', 'base_coordinate': [760, 224]})
        s.message(0x200, 760 * s.factor, 224 * s.factor)
        time.sleep(1.5)
        s.shot('region-hover', move_cursor=False)
        if s.i(0x659f51) != initial:
            raise RuntimeError('Hover changed initial region focus')
        s.result['actions'].append({'action': 'open-grimoire', 'base_coordinate': [976, 66]})
        s.click_base(976, 66)
        time.sleep(1)
        close = [c for c in s.controls() if c['vtable'] == '0x5c6bd0'
                 and c['rect'][:2] == [1088 * s.factor, 286 * s.factor]]
        if len(close) != 1:
            raise RuntimeError('Grimoire close control absent or ambiguous')
        s.shot('grimoire')
        s.result['actions'].append({'action': 'close-grimoire', 'base_coordinate': [1098, 330]})
        s.click_base(1098, 330)
        time.sleep(.7)
        s.require_rect([x * s.factor for x in (940, 30, 1012, 102)])
        s.shot('return-initial-focus')
        if s.i(0x659f51) != initial:
            raise RuntimeError('Return changed initial region focus')
    return s.records


def make_pairs(out, records, screens=SCREENS):
    from PIL import Image, ImageChops
    pairs = {}
    for name in screens:
        a = records['1.0'][name]
        b = records['1.1'][name]
        with Image.open(a['output']) as left, Image.open(b['output']) as right:
            left, right = left.convert('RGB'), right.convert('RGB')
            pair = Image.new('RGB', (5120, 1440))
            pair.paste(left, (0, 0)); pair.paste(right, (2560, 0))
            path = out / (name + '-pair.png')
            pair.save(path)
            diff = ImageChops.difference(left, right)
            diff.save(out / (name + '-difference.png'))
            hist = ImageChops.lighter(ImageChops.lighter(*diff.split()[:2]), diff.split()[2]).histogram()
        if a['region_id'] != b['region_id'] and name != 'grimoire':
            raise RuntimeError('Paired initial map region differs: ' + name)
        pairs[name] = dict(pair=str(path), changed_fraction_over_16=sum(hist[17:]) / sum(hist),
                           region_ids=[a['region_id'], b['region_id']],
                           note='Difference metric is evidence, not a visual acceptance threshold')
    return pairs


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--verify-only', action='store_true', help='Read/hash packages only; never launch or stage')
    mode.add_argument('--run', action='store_true', help='Explicitly launch paired bounded background captures')
    p.add_argument('--baseline-package', type=Path, default=BASE, help='Immutable 1.0 release layout to clone')
    p.add_argument('--candidate-package', type=Path, default=CANDIDATE, help='1.1 launcher/manifest and sibling runtime')
    p.add_argument('--candidate-manifest-sha256', default=CANDIDATE_MANIFEST,
                   help='Reviewed exact manifest digest after map install; engine allowlist remains fixed')
    p.add_argument('--out', type=Path, help='Fresh output directory under modernization/logs; must not exist')
    p.add_argument('--seconds', type=int, default=90, help='Per-game deadline, including startup (30..180; default 90)')
    p.add_argument('--fixture', type=Path, help='Optional identical .sav staged in both copies; not loaded by this UI case')
    p.add_argument('--fixture-sha256', help='Required pinned SHA-256 when supplying --fixture')
    p.add_argument('--candidate-in-place',action='store_true',help='Use verified isolated candidate path to preserve compositor path gate; backup and restore mutable state')
    p.add_argument('--case',choices=['new-game-ui','realm-loaded','settings-battle','portmanteau','portmanteau-full'],default='new-game-ui')
    p.add_argument('--baseline-capture', type=Path, help='Reuse hash-verified earlier baseline-first captured case; candidate still runs after it')
    args = p.parse_args(argv)
    ctypes.windll.user32.SetProcessDPIAware()
    if not 30 <= args.seconds <= 180:
        p.error('--seconds must be 30..180')
    if bool(args.fixture) != bool(args.fixture_sha256):
        p.error('--fixture and --fixture-sha256 must be supplied together')
    screens={'realm-loaded':REALM_SCREENS,'settings-battle':CORE_SCREENS,'portmanteau':PORT_SCREENS,'portmanteau-full':PORT_FULL_SCREENS}.get(args.case,SCREENS)
    if args.case in ('realm-loaded','settings-battle','portmanteau','portmanteau-full') and not args.fixture:p.error('fixture cases require identical hash-verified --fixture')
    if args.run and args.case=='settings-battle' and not args.candidate_in_place:p.error('Current path-gated compositor requires --candidate-in-place for battle acceptance')
    if args.fixture and (args.fixture.suffix.lower() != '.sav' or sha(args.fixture) != args.fixture_sha256):
        p.error('Fixture must be a hash-verified .sav')
    identities = [verify_package(args.baseline_package, '1.0', BASE_MANIFEST),
                  verify_package(args.candidate_package, '1.1', args.candidate_manifest_sha256)]
    if sha(DIAGNOSTIC) != DIAGNOSTIC_SHA:
        raise RuntimeError('Baseline diagnostic wrapper changed')
    if args.verify_only:
        print(json.dumps(identities, indent=2))
        return 0
    out = (args.out or ROOT / 'modernization/logs/remastered-ui' / str(time.time_ns())).resolve()
    if not out.is_relative_to((ROOT / 'modernization/logs').resolve()):
        p.error('--out must be under modernization/logs')
    # Capture source save/config hashes to audit preservation even on failure.
    source_before = {str(f): sha(f) for i in identities for f in files(Path(i['package']) / 'runtime')
                     if mutable_name(f.relative_to(Path(i['package']) / 'runtime').as_posix())}
    out.mkdir(parents=True, exist_ok=False)
    result = dict(status='preparing', identities=identities, case=args.case,
                  acceptance='pending user review; no automated visual acceptance',
                  fixture_sha256=args.fixture_sha256, per_session_seconds=args.seconds)
    records = {}
    try:
        cls = session_class()
        for identity in identities:  # baseline always completes before candidate starts
            label = identity['version']
            if label == '1.0' and args.baseline_capture:
                old=json.loads(args.baseline_capture.read_text(encoding='utf-8'))
                if old['status']!='captured' or not old['restored'] or old['cleanup_errors']:
                    raise RuntimeError('Prior baseline capture not restored/passed')
                for key in ('manifest_sha256','launcher_sha256','engine_sha256'):
                    if old['identity'][key]!=identity[key]:raise RuntimeError('Prior baseline identity mismatch: '+key)
                if args.case in ('realm-loaded','settings-battle','portmanteau','portmanteau-full') and old.get('fixture_sha256')!=args.fixture_sha256:
                    raise RuntimeError('Prior baseline fixture differs')
                prior=old['screens']
                if set(prior)!=set(screens):raise RuntimeError('Prior baseline case differs')
                for row in prior.values():
                    if sha(row['output'])!=row['sha256']:raise RuntimeError('Prior baseline screenshot changed')
                records[label]=prior
                result['reused_baseline_capture']=str(args.baseline_capture.resolve())
                continue
            if label=='1.1' and args.candidate_in_place:
                if Path(identity['package']).resolve()!=CANDIDATE.resolve():raise RuntimeError('In-place only allowed for known isolated candidate')
                runtime=CANDIDATE/'runtime'
                if args.fixture and (not (runtime/'Save'/args.fixture.name).is_file() or sha(runtime/'Save'/args.fixture.name)!=args.fixture_sha256):
                    raise RuntimeError('Use existing identical candidate save for in-place testing')
                result['candidate_in_place']=True
            else:
                runtime = stage(identity, out / ('package-' + label), args.fixture)
            if args.fixture and sha(runtime / 'Save' / args.fixture.name) != args.fixture_sha256:
                raise RuntimeError('Staged fixture identity changed')
            # Recheck source identity after copying, before launching any game.
            verify_package(Path(identity['package']), label, identity['manifest_sha256'])
            session=cls(identity,runtime,out/label,args.seconds)
            flow={'realm-loaded':capture_realm_flow,'settings-battle':capture_core_flow,'portmanteau':capture_port_flow,'portmanteau-full':capture_port_full_flow}.get(args.case)
            records[label]=flow(session,args.fixture) if flow else capture_flow(session)
        if args.case=='settings-battle':result['minimap_pixels']=verify_minimap_pixels(records)
        result['pairs'] = make_pairs(out, records, screens)
        result['status'] = 'captured'
    except BaseException as e:
        result.update(status='failed', error=str(e))
        raise
    finally:
        changed = [name for name, digest in source_before.items()
                   if not Path(name).is_file() or sha(name) != digest]
        result['source_changes'] = changed
        if changed:
            result['status'] = 'failed'
        write_json(out / 'comparison.json', result)
        print(out / 'comparison.json')
        if changed:
            raise RuntimeError('Source state changed during comparison: ' + ', '.join(changed))
    return 0


if __name__ == '__main__':
    sys.exit(main())
