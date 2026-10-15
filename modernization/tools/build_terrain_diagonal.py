"""Stage an isolated v22-derived terrain-diagonal playtest; never install it."""
from pathlib import Path
import hashlib,json,shutil,subprocess
import pefile
from compare_hd_baseline import baseline_identity

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'modernization/playtests/terrain-diagonal-v1'
BUILD=ROOT/'modernization/build/terrain-diagonal-v1'
SHA='f9c90c345fe295802794b75822b53440d5b84abe11d491115e7e4a2d511f2eaf'

def main():
    latest=baseline_identity();assert latest['files'][latest['entry']]==SHA
    BUILD.mkdir(parents=True,exist_ok=True)
    launcher=ROOT/latest['entry'];pe=pefile.PE(str(launcher))
    for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if kind.id==10:
            for resource in kind.directory.entries:
                if resource.id in (101,102):
                    d=resource.directory.entries[0].data.struct
                    (BUILD/f'original-{resource.id}.dll').write_bytes(pe.get_data(d.OffsetToData,d.Size))
    source=(ROOT/'modernization/runtime/wide169/launcher.cpp').read_text()
    source=source.replace('1d2df6135238dec69f6ec74280440a06b43c66353c886f42633f4143d710b16f',latest['files'][latest['engine']])
    needle='    CloseHandle(pi.hThread);\n    WaitForSingleObject(pi.hProcess,INFINITE);'
    assert source.count(needle)==1
    source=source.replace(needle,'''    if (!sha256(game+L"\\\\terrain_diagonal.dll",L"TERRAIN_SHA") || !inject(pi,game+L"\\\\terrain_diagonal.dll")) {
        TerminateProcess(pi.hProcess,1);fail(L"Terrain candidate module failed.");return 11;
    }
'''+needle)
    (BUILD/'launcher-template.cpp').write_text(source)
    (BUILD/'original.rc').write_text('101 RCDATA "original-101.dll"\n102 RCDATA "original-102.dll"\n')
    vc=r'C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat'
    src=ROOT/'modernization/runtime/terrain_diagonal/terrain_diagonal.cpp'
    (BUILD/'compile-dll.cmd').write_text(f'@echo off\ncall "{vc}" x86 >nul\nif errorlevel 1 exit /b 1\ncl /nologo /LD /O2 /EHsc /W4 "{src}" /Fo"terrain.obj" /link /OUT:"terrain_diagonal.dll"\n')
    subprocess.run(['cmd','/c','compile-dll.cmd'],cwd=BUILD,check=True,timeout=90)
    digest=hashlib.sha256((BUILD/'terrain_diagonal.dll').read_bytes()).hexdigest()
    (BUILD/'launcher.cpp').write_text(source.replace('TERRAIN_SHA',digest))
    (BUILD/'compile-entry.cmd').write_text(f'@echo off\ncall "{vc}" x86 >nul\nif errorlevel 1 exit /b 1\nrc /nologo /fooriginal.res original.rc\nif errorlevel 1 exit /b 1\ncl /nologo /O2 /EHsc /std:c++17 /W4 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER launcher.cpp original.res /link /SUBSYSTEM:WINDOWS /OUT:"Chaos-Terrain-Preview.exe" bcrypt.lib user32.lib\n')
    subprocess.run(['cmd','/c','compile-entry.cmd'],cwd=BUILD,check=True,timeout=90)
    if not OUT.exists():
        OUT.mkdir();(OUT/'game').mkdir()
        subprocess.run(['robocopy',str(ROOT/'game-wide169'),str(OUT/'game-wide169'),'/E','/XJ','/XD','modernization','ss','/NFL','/NDL','/NJH','/NJS','/R:1','/W:1'],timeout=300,check=False)
        (OUT/'game-wide169/modernization/logs').mkdir(parents=True)
        (OUT/'game-wide169/modernization/config').mkdir(parents=True)
        for p in (ROOT/'modernization/config').glob('qol*'):shutil.copy2(p,OUT/'game-wide169/modernization/config'/p.name)
    shutil.copy2(BUILD/'terrain_diagonal.dll',OUT/'game-wide169/terrain_diagonal.dll')
    shutil.copy2(BUILD/'Chaos-Terrain-Preview.exe',OUT/'game/Chaos-Terrain-Preview.exe')
    # Keep original launcher available as the isolated rollback/control entry.
    shutil.copy2(launcher,OUT/'game/Chaos-Wide169-Trial.exe')
    manifest=dict(parent=latest,experimental=True,automatic_saved_route_refresh=False,
      files={p.relative_to(OUT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'game/Chaos-Terrain-Preview.exe',OUT/'game/Chaos-Wide169-Trial.exe',OUT/'game-wide169/Chaos-Wide169-engine.exe',OUT/'game-wide169/terrain_diagonal.dll')},
      embedded_parent_modules={str(i):hashlib.sha256((BUILD/f'original-{i}.dll').read_bytes()).hexdigest() for i in (101,102)})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(OUT)

if __name__=='__main__':main()
