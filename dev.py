"""Portable, offline source checks and x86 builds for the frozen 1.1 extensions.

This tool never installs, starts or modifies the game. All generated files stay
under out/; input player files are read only. Historical scripts are separate.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'out'
INDEX = json.loads((ROOT/'modernization/docs/source-index.json').read_text(encoding='utf-8-sig'))
GROUPS = {g['component']: ROOT/g['source_root'] for g in INDEX['groups']}
CORE = ['101', '102', '103', 'terrain', 'fmv', 'png', 'wrapper']
DLLS = {'101': 'repath.dll', '102': 'qol_bindings.dll', '103': 'ai_diagnostics.dll',
        'terrain': 'terrain_diagonal.dll', 'fmv': 'fmv_h264.dll', 'png': 'png_assets.dll', 'wrapper': 'ddraw.dll'}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(args, cwd, env=None, timeout=300):
    args = [str(a) for a in args]
    if env is not None:
        executable = shutil.which(args[0], path=env.get('PATH'))
        if not executable:
            raise RuntimeError(f'Build tool is missing from the MSVC environment: {args[0]}')
        args[0] = executable
    subprocess.run(args, cwd=cwd, env=env, check=True, timeout=timeout)

def audit():
    manifest = json.loads((ROOT/'source-distribution.json').read_text(encoding='utf-8'))
    for item in manifest['files']:
        path = ROOT/item['path']
        if not path.is_file() or digest(path) != item['sha256']:
            raise RuntimeError(f'Missing or changed distribution file: {item["path"]}')
    # Check quoted include dependencies for the exact release snapshot groups.
    missing = []
    for group in INDEX['groups']:
        source = ROOT/group['source_root']
        for item in group['materials']:
            p = ROOT/item['path']
            if p.suffix.lower() not in {'.cpp', '.c', '.h', '.inc'}:
                continue
            for include in re.findall(r'^\s*#\s*include\s*"([^"]+)"', p.read_text(encoding='utf-8-sig', errors='replace'), re.M):
                if not any((base/include).is_file() for base in (p.parent, source, source/'inc', source/'src/detours', ROOT/'modernization/runtime/hd11')):
                    # MSVC/Windows SDK supplies this quoted header.
                    if include.lower() not in {'targetver.h', 'windows.h', 'winver.h', 'd3d9types.h'}:
                        missing.append(f'{p.relative_to(ROOT)} -> {include}')
    if missing:
        raise RuntimeError('Unresolved quoted includes:\n'+'\n'.join(missing))
    print(f'PASS: {len(manifest["files"])} distribution hashes; release-source quoted includes resolved.')

def prepare(release):
    import pefile
    release = release.resolve(strict=True)
    for name, expected in INDEX['baseline']['files'].items():
        if digest(release/name) != expected:
            raise RuntimeError(f'Unknown player version: {name}')
    launcher = release/'MagicMayhem-Remastered.exe'
    inputs = OUT/'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    with pefile.PE(str(launcher)) as pe:
        resources = {}
        for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            for entry in kind.directory.entries:
                data = entry.directory.entries[0].data.struct
                resources[(kind.id, entry.id)] = pe.get_data(data.OffsetToData, data.Size)
        for module, expected in INDEX['baseline']['embedded_modules'].items():
            data = resources[(10, int(module))]
            if hashlib.sha256(data).hexdigest() != expected:
                raise RuntimeError(f'Unknown embedded module: {module}')
            (inputs/DLLS[module]).write_bytes(data)
        groups = [data for (kind, _), data in resources.items() if kind == 14]
        if len(groups) != 1:
            raise RuntimeError('Expected one launcher icon group')
        group = groups[0]
        count = struct.unpack_from('<H', group, 4)[0]
        directory, images = bytearray(group[:6]), bytearray()
        for i in range(count):
            entry = group[6+14*i:20+14*i]
            icon_id = struct.unpack_from('<H', entry, 12)[0]
            data = resources[(3, icon_id)]
            directory.extend(entry[:12]+struct.pack('<I', 6+16*count+len(images)))
            images.extend(data)
        (inputs/'remastered.ico').write_bytes(directory+images)
    with pefile.PE(str(release/'runtime/Chaos-Wide169-engine.exe')) as pe:
        data = bytearray(pe.get_data(0x58b3e0-pe.OPTIONAL_HEADER.ImageBase, 0xd8))
    # Relocate the ten absolute-address high bytes for the isolated native harness.
    for offset in (25, 103, 111, 129, 135, 145, 171, 177, 183, 193):
        if data[offset] != 0:
            raise RuntimeError('Unexpected native fixture address')
        data[offset] = 0x20
    expected = next(m['sha256'] for g in INDEX['groups'] for m in g['materials'] if m['path'].endswith('/native_destroy.bin'))
    if hashlib.sha256(data).hexdigest() != expected:
        raise RuntimeError('Unexpected relocated native Destroy bytes')
    (inputs/'native_destroy.bin').write_bytes(data)
    # Save only file identities, never a user's path, settings, saves or credentials.
    (inputs/'identity.json').write_text(json.dumps(INDEX['baseline'], indent=2)+'\n', encoding='utf-8')
    print('PASS: exact 1.1 player inputs verified; embedded modules, icon and native fixture extracted to out/inputs/.')

def msvc_environment():
    if os.name != 'nt':
        raise RuntimeError('Builds require Windows and MSVC x86/Windows SDK.')
    override = os.environ.get('MM_VCVARSALL')
    if override:
        vcvars = Path(override).resolve(strict=True)
    else:
        vswhere = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
        install = subprocess.check_output([str(vswhere), '-latest', '-products', '*', '-requires',
            'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'], text=True).strip()
        if not install:
            raise RuntimeError('Install Visual Studio C++ x86 build tools and Windows SDK, or set MM_VCVARSALL.')
        vcvars = Path(install)/'VC/Auxiliary/Build/vcvarsall.bat'
    OUT.mkdir(exist_ok=True)
    batch = OUT/'msvc-env.cmd'
    batch.write_text(f'@echo off\ncall "{vcvars}" x86 >nul\nif errorlevel 1 exit /b 1\nset\n', encoding='utf-8')
    output = subprocess.check_output(['cmd.exe', '/d', '/c', str(batch)], text=True, errors='replace', timeout=120)
    # Windows environment keys are case-insensitive. A plain dict must not
    # contain both inherited PATH and vcvars' Path.
    env = {key.upper(): value for key, value in os.environ.items()}
    for line in output.splitlines():
        if '=' in line and not line.startswith('='):
            key, value = line.split('=', 1)
            env[key.upper()] = value
    if env.get('VSCMD_ARG_TGT_ARCH') != 'x86':
        raise RuntimeError('Expected MSVC x86 environment')
    return env

def compile_cpp(directory, sources, output, env, defines=(), libraries=(), dll=True, includes=(), flags=(), link=()):
    directory.mkdir(parents=True, exist_ok=True)
    args = ['cl', '/nologo', '/O2', '/EHsc', '/std:c++17', '/W4']
    if dll:
        args.append('/LD')
    args += list(flags)+['/D'+d for d in defines]+['/I'+str(p) for p in includes]+list(sources)
    args += ['/link', '/OUT:'+str(directory/output), '/MAP:'+str(directory/(Path(output).stem+'.map'))]+list(link)+list(libraries)
    run(args, directory, env)

def build(component, env):
    directory = OUT/component
    if component == '101':
        source = GROUPS['101']
        names = ['repath_multiunit_trial.cpp', 'render_replay_trial.cpp', 'clock_trial.cpp', 'logic_time_trial.cpp', 'game_time_trial.cpp']
        compile_cpp(directory, [source/n for n in names], DLLS[component], env, defines=['MM_COMBINED', 'MM_ALL_IN_ONE'])
    elif component == '102':
        source = GROUPS['launcher_and_102']
        names = ['qol_bindings.cpp', 'mixed_ui_fonts.cpp', 'campaign_ui.cpp', 'port_drag.cpp', 'confirm_dialog.cpp',
            'qwen_highlight.cpp', 'window_close.cpp', 'surface_lifecycle.cpp', 'portrait_sprite_ready.cpp',
            'ai_budget.cpp', 'ai_danger_refresh.cpp', 'options_resolution.cpp', 'options_window.cpp', 'options_speed.cpp', 'options_render.cpp']
        compile_cpp(directory, [source/n for n in names], DLLS[component], env, libraries=['user32.lib'])
    elif component == '103':
        compile_cpp(directory, [GROUPS['103']/'ai_diagnostics.cpp'], DLLS[component], env, libraries=['bcrypt.lib', 'user32.lib'])
    elif component == 'terrain':
        compile_cpp(directory, [GROUPS['terrain']/'terrain_diagonal.cpp'], DLLS[component], env)
    elif component == 'fmv':
        compile_cpp(directory, [GROUPS['fmv']/'fmv_h264.cpp'], DLLS[component], env, libraries=['user32.lib', 'gdi32.lib'])
    elif component == 'png':
        compile_cpp(directory, [GROUPS['general_png']/'png_assets.cpp'], DLLS[component], env,
                    flags=['/MT'], libraries=['ole32.lib', 'windowscodecs.lib'])
    elif component == 'wrapper':
        directory.mkdir(parents=True, exist_ok=True)
        source = directory/'source'
        shutil.copytree(GROUPS['wrapper'], source, dirs_exist_ok=True)
        project = source/'cnc-ddraw.vcxproj'
        ns = '{http://schemas.microsoft.com/developer/msbuild/2003}'
        ET.register_namespace('', ns[1:-1])
        tree = ET.parse(project)
        # Build only in out/: no upstream prebuild Git mutation or postbuild copy.
        for parent in tree.iter():
            for child in list(parent):
                if child.tag in {ns+'PreBuildEvent', ns+'PostBuildEvent'}:
                    parent.remove(child)
        tree.write(project, encoding='utf-8', xml_declaration=True)
        run(['MSBuild', project, '/p:Configuration=Release', '/p:Platform=Win32', '/m', '/v:minimal', '/nologo'], directory, env, timeout=600)
        shutil.copy2(source/'bin/Release/ddraw.dll', directory/DLLS[component])
    elif component == 'launcher':
        inputs = OUT/'inputs'
        if not (inputs/'identity.json').is_file():
            raise RuntimeError('Run prepare --release-root <your exact 1.1 player folder> first.')
        directory.mkdir(parents=True, exist_ok=True)
        for module in ['101', '102', '103']:
            built = OUT/module/DLLS[module]
            shutil.copy2(built if built.is_file() else inputs/DLLS[module], directory/DLLS[module])
        shutil.copy2(inputs/'remastered.ico', directory/'remastered.ico')
        (directory/'release.rc').write_text('1 ICON "remastered.ico"\n101 RCDATA "repath.dll"\n102 RCDATA "qol_bindings.dll"\n103 RCDATA "ai_diagnostics.dll"\n', encoding='ascii')
        source = (GROUPS['launcher_and_102']/'release_launcher.cpp').read_text(encoding='utf-8-sig')
        # Re-pin only explicitly built dependencies, keeping all identity gates.
        for name in ['terrain', 'fmv', 'png']:
            binary = OUT/name/DLLS[name]
            if binary.is_file():
                original = next(g['matching_artifact']['sha256'] for g in INDEX['groups']
                                if g['component'] == {'png': 'general_png'}.get(name, name))
                if source.count(original) != 1:
                    raise RuntimeError('Unexpected dependency pin occurrence')
                source = source.replace(original, digest(binary))
        generated = directory/'release_launcher.cpp'
        generated.write_text(source, encoding='utf-8')
        run(['rc', '/nologo', '/forelease.res', 'release.rc'], directory, env)
        defines = ['MM_ANIMATION_MOTION_LAUNCHER', 'MM_LAYER_LAUNCHER', 'MM_FULL_TRIAL_LAUNCHER', 'MM_INSTALLED_LAUNCHER']
        compile_cpp(directory, [generated, directory/'release.res'], 'MagicMayhem-Remastered.exe', env,
                    defines=defines, libraries=['bcrypt.lib', 'user32.lib'], dll=False, link=['/SUBSYSTEM:WINDOWS'])
    else:
        raise RuntimeError(f'Unknown component: {component}')

def tests(env):
    directory = OUT/'tests'
    source = GROUPS['launcher_and_102']
    compile_cpp(directory, [source/'surface_registry_test.cpp'], 'surface_registry_test.exe', env, dll=False)
    run([directory/'surface_registry_test.exe'], directory)
    compile_cpp(directory, [ROOT/'modernization/tests/movement_timing_test.cpp'], 'movement_timing_test.exe', env,
                dll=False, includes=[GROUPS['101']])
    run([directory/'movement_timing_test.exe'], directory)
    fixture = OUT/'inputs/native_destroy.bin'
    if not fixture.is_file():
        raise RuntimeError('Native lifecycle test needs prepare --release-root first.')
    shutil.copy2(fixture, directory/'native_destroy.bin')
    compile_cpp(directory, [source/'surface_lifecycle_native_test.cpp', source/'surface_lifecycle_test_hooks.cpp'],
                'surface_lifecycle_native_test.exe', env, dll=False, link=['/BASE:0x10000000', '/DYNAMICBASE:NO'])
    run([directory/'surface_lifecycle_native_test.exe'], directory)
    print('PASS: surface registry, movement timing, exact native Destroy lifecycle harnesses. No game was started.')

def report():
    import pefile
    artifacts = []
    for name, filename in list(DLLS.items())+[('launcher', 'MagicMayhem-Remastered.exe')]:
        path = OUT/name/filename
        if not path.is_file():
            continue
        with pefile.PE(str(path)) as pe:
            if pe.FILE_HEADER.Machine != 0x14c:
                raise RuntimeError(f'Non-x86 output: {filename}')
        artifacts.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path), 'machine': 'x86'})
    if artifacts:
        (OUT/'build-report.json').write_text(json.dumps({'artifacts': artifacts,
            'gameplay_acceptance': 'pending; offline build only'}, indent=2)+'\n', encoding='utf-8')
    print(f'PASS: {len(artifacts)} x86 artifacts recorded in out/build-report.json; runtime acceptance remains pending.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('audit')
    prep = sub.add_parser('prepare')
    prep.add_argument('--release-root', type=Path, required=True)
    build_parser = sub.add_parser('build')
    build_parser.add_argument('--component', choices=CORE+['launcher', 'all'], default='all')
    sub.add_parser('test')
    args = parser.parse_args()
    if args.command == 'audit':
        audit()
    elif args.command == 'prepare':
        prepare(args.release_root)
    else:
        env = msvc_environment()
        if args.command == 'test':
            tests(env)
        else:
            targets = CORE+['launcher'] if args.component == 'all' else [args.component]
            for name in targets:
                print('BUILD', name, flush=True)
                build(name, env)
            report()

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
