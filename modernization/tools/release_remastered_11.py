"""Freeze current1.1 into a clean, independently verified player release."""
from pathlib import Path
import json,shutil,subprocess,hashlib,re,os
import pefile
import build_remastered_11 as b
from install_11_minimap_v2 import resources

OUT=b.ROOT/'modernization/releases/remastered-1.1'
STAGE=OUT/'package'
DEST=Path('D:/Games/Magic&Mayham_Remastered_1.1')
SOURCE=b.TARGET
RUNTIME=SOURCE/'runtime'
ENTRY='MagicMayhem-Remastered.exe'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def inventory(root):
    result={}
    for directory,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            p=Path(directory)/name
            assert not p.is_symlink() and not p.is_junction(),'Release cannot contain junctions'
        for name in files:
            p=Path(directory)/name;result[p.relative_to(root).as_posix()]=sha(p)
    return result

def excluded(name):
    lower=name.lower()
    return (lower.startswith(('save/','ss/','modernization/logs/','cfg/encrypted/'))
        or lower in {'uninst.isu','wide169-lab.json','readme.txt','readme.wri','fmv-h264-events.jsonl'}
        or Path(name).suffix.lower() in {'.tmp','.log','.csv','.dmp','.obj','.pdb','.bak','.py','.cpp','.lib','.exp'})

def main():
    assert DEST.resolve()==Path('D:/Games/Magic&Mayham_Remastered_1.1').resolve()
    assert not DEST.exists() or not any(DEST.iterdir()),'Refuse overwriting existing release/user files'
    assert not OUT.exists(),'Keep frozen release immutable'
    m=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
    before_manifest=sha(SOURCE/'manifest.json');before_entry=sha(SOURCE/'MagicMayhem-Remastered-1.1.exe')
    assert before_entry==m['launcher_sha256']
    assert sha(RUNTIME/'Chaos-Wide169-engine.exe')==m['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
    # Capture a read-only file plan. Running-game caches are replaced from the
    # immutable package; static resources must match the installed manifest.
    plan=[];omitted=[]
    for name,digest in m['files'].items():
        if excluded(name):omitted.append(name);continue
        p=RUNTIME/name
        if name in {'AI/Brain.dat','AI/EXPERIEN.DAT'} or not p.exists():
            p=b.BASE/'runtime'/name
            assert sha(p)==digest,'Unknown missing/static fallback '+name
        if name not in {'CFG/prefs.cfg','ddraw.ini','modernization/config/qol-hotkeys.json'}:
            assert sha(p)==digest,'Unverified resource '+name
        plan.append((name,p,sha(p)))
    protected=json.loads((b.ROOT/'modernization/backups/remastered-1.1-p1/protected.json').read_text(encoding='utf-8'))
    for path,digest in protected.items():assert sha(Path(path))==digest
    OUT.mkdir();STAGE.mkdir();rt=STAGE/'runtime';rt.mkdir()
    for name,p,digest in plan:
        target=rt/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        assert sha(target)==digest,'Source changed during release copy: '+name
    (rt/'Save').mkdir();(STAGE/'Documentation').mkdir()
    for name in ['Readme.txt','Readme.wri']:
        shutil.copy2(b.BASE/'runtime'/name,STAGE/'Documentation'/('Community-'+name))
    current=b.ROOT/'modernization/build/remastered-1.1-fmv-h264'
    source=(current/'launcher.cpp').read_text(encoding='utf-8')
    assert resources(SOURCE/'MagicMayhem-Remastered-1.1.exe')==resources(current/'MagicMayhem-Remastered-1.1.exe')
    assert sha(current/'MagicMayhem-Remastered-1.1.exe')==before_entry
    # Diagnostic flags inherited by a shell must not accidentally activate
    # capture/input/log behavior in a player release. Functional flags below
    # are still assigned identically by the existing launcher.
    needle='    STARTUPINFOW startup={};startup.cb=sizeof(startup);'
    clean='''    const wchar_t* diagnostic_flags[]={L"MM_PROBE_BACKGROUND_INPUT",L"MM_PROBE_TRACE",L"MM_PROBE_FRAME_HASH",L"MM_PROBE_SURFACE_CALLS",L"MM_REALM_HIGHLIGHT_TRACE"};
    for(auto flag:diagnostic_flags)SetEnvironmentVariableW(flag,nullptr);
'''
    source=b.replace_once(source,needle,clean+needle)
    (OUT/'launcher.cpp').write_text(source,encoding='utf-8')
    for key,name in [(101,'repath.dll'),(102,'qol_bindings.dll')]:
        (OUT/name).write_bytes(resources(SOURCE/'MagicMayhem-Remastered-1.1.exe')[key])
    icon=b.ROOT/'modernization/releases/remastered-1.0/remastered.ico';shutil.copy2(icon,OUT/'remastered.ico')
    (OUT/'release.rc').write_text('1 ICON "remastered.ico"\n101 RCDATA "repath.dll"\n102 RCDATA "qol_bindings.dll"\n')
    cmd=(current/'build.cmd').read_text().replace('candidate.res','release.res').replace('combined.rc','release.rc').replace('/OUT:MagicMayhem-Remastered-1.1.exe','/OUT:package\\'+ENTRY)
    (OUT/'build.cmd').write_text(cmd)
    subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True,timeout=120)
    assert resources(STAGE/ENTRY)==resources(SOURCE/'MagicMayhem-Remastered-1.1.exe')
    readme='''Magic & Mayhem Remastered 1.1
魔法师传奇 重制版

开始游戏
双击 MagicMayhem-Remastered.exe。请保留整个文件夹的目录结构；
移动或复制游戏时，将整个文件夹一起移动或复制。

本版主要改动
• 菜单、魔法书、旅行箱与大地图采用高清素材和更清晰的文字。
• 界面以 1920×1440 原生内容显示，居中于 2560×1440。
• 战斗保留 1280×720 场景和 HUD，整体放大至 2560×1440。
• 五部过场视频升级为 2560×1440，保留原版视频作为播放回退。
• 保留法术快捷键、多单位寻路、编队移动与遮挡半透明显示。
• 修正小地图点击定位、头像施法及多处界面布局与重绘问题。
• 保留中文文本、音乐和原版存档格式。

法术快捷键
在旅行箱中，将鼠标移到法术槽位上并按下要绑定的键；
同一个键可转移到其他槽位，按 Delete 清除当前槽位的绑定。
战斗中按绑定键选择法术，左键施法，右键取消。
支持对自己施放的法术，可快速连按两次绑定键对自己施法。

显示与存档
默认以 2560×1440 窗口显示；可运行 runtime\\cnc-ddraw config.exe
调整窗口和全屏显示。此设置调整输出显示，独立的 1K/2K/4K
原生界面切换尚未提供。
存档位于 runtime\\Save，可将旧版 .sav 存档复制到此目录。
更新或替换游戏前，建议先备份存档。

已知问题
读档后偶发卡住仍在排查；若遇到请保留现场并反馈。
联机模式尚未完成适配验证，建议使用单人模式。
'''
    (STAGE/'readme.txt').write_text(readme,encoding='utf-8-sig')
    verify='''$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$manifest = Get-Content -LiteralPath (Join-Path $root 'release-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$failures = @()
$checked = 0
foreach ($entry in $manifest.files.PSObject.Properties) {
    if ($entry.Name -in $manifest.mutable_files) { continue }
    $path = Join-Path $root $entry.Name
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) { $failures += "Missing: $($entry.Name)"; continue }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) { $failures += "Changed: $($entry.Name)" }
    $checked++
}
if ($failures.Count) { $failures | Write-Output; throw "$($failures.Count) static files differ." }
Write-Output "Verified $checked static release files. Player settings/saves/caches excluded."
'''
    # The eleven plaintext CFGs are consumed on first startup; generated
    # encrypted copies are runtime caches. Validate exact plaintext now, but
    # allow their disappearance in the player's post-startup integrity check.
    consumed=[r for r,_,_ in plan if r.startswith('CFG/') and (rt/'CFG/Encrypted'/Path(r).name).exists()]
    consumed=[r for r,_,_ in plan if r.startswith('CFG/') and (b.BASE/'runtime/CFG/Encrypted'/Path(r).name).exists()]
    assert len(consumed)==11
    (STAGE/'verify-files.ps1').write_text(verify,encoding='utf-8-sig')
    modules={str(k):hashlib.sha256(v).hexdigest() for k,v in resources(STAGE/ENTRY).items()}
    pe=pefile.PE(str(STAGE/ENTRY))
    try:
        assert pe.FILE_HEADER.Machine==0x14c
        types={e.id:e for e in pe.DIRECTORY_ENTRY_RESOURCE.entries};assert 3 in types and 14 in types
        assert len(types[3].directory.entries)==4
    finally:pe.close()
    assert len(list(STAGE.glob('*.exe')))==1
    assert not any((rt/'Save').iterdir())
    assert re.search(rb'(?m)^MaxFramesPerSec\s*=\s*30\s*$',(rt/'CFG/prefs.cfg').read_bytes())
    # Runtime libraries can use system DLLs but never require the project tree.
    imports={};unresolved=[]
    for p in list(STAGE.rglob('*.exe'))+list(STAGE.rglob('*.dll'))+list(OUT.glob('*.dll')):
        pe=pefile.PE(str(p))
        try:
            names=[]
            for kind in ['DIRECTORY_ENTRY_IMPORT','DIRECTORY_ENTRY_DELAY_IMPORT']:
                for entry in getattr(pe,kind,[]):
                    name=entry.dll.decode();names.append(name)
                    if not any((directory/name).exists() for directory in [p.parent,rt,Path('C:/Windows/SysWOW64'),Path('C:/Windows/System32')]) and not name.lower().startswith(('api-ms-','ext-ms-')):unresolved.append((p.name,name))
            imports[p.name]=sorted(set(names))
        finally:pe.close()
    assert not unresolved,unresolved
    files=inventory(STAGE)
    # .map under Realms is native game data, never a linker-map artifact.
    expected_maps={n:d for n,d in m['files'].items() if n.lower().startswith('realms/') and n.lower().endswith('.map')}
    assert expected_maps and all(files.get('runtime/'+n)==d for n,d in expected_maps.items())
    assert not any(excluded(n.removeprefix('runtime/')) for n in files if n.startswith('runtime/'))
    mutable=['runtime/'+r for r in consumed+['CFG/prefs.cfg','ddraw.ini','modernization/config/qol-hotkeys.json','AI/Brain.dat','AI/EXPERIEN.DAT']]
    release=dict(version='1.1',date='2026-10-01',launcher=ENTRY,launcher_sha256=sha(STAGE/ENTRY),
        engine_sha256=m['engine_sha256'],embedded_modules=modules,native_ui=[1920,1440],ui_origin=[320,0],native_battle=[1280,720],output=[2560,1440],
        files=files,mutable_files=mutable,source_manifest_sha256=before_manifest,source_launcher_sha256=before_entry,
        validation='Build, resources, imports and static integrity passed; no gameplay launched for release',
        known_issues=['Intermittent load AV followed by OGG shutdown wait unresolved','Campaign film triggers pending user verification','Multiplayer and native resolution switching unvalidated/unimplemented'])
    b.write(STAGE/'release-manifest.json',release)
    b.write(OUT/'provenance.json',dict(source_manifest_sha256=before_manifest,source_launcher_sha256=before_entry,omitted=omitted,
        policy='clean manifest-only runtime; empty Save; no caches/logs/test assets; active generated assets and AVI fallback retained',source_files={n:h for n,_,h in plan}))
    # Freeze only immutable sources; user may continue using the source game.
    assert sha(SOURCE/'manifest.json')==before_manifest and sha(SOURCE/'MagicMayhem-Remastered-1.1.exe')==before_entry
    for path,digest in protected.items():assert sha(Path(path))==digest
    DEST.mkdir(exist_ok=True)
    shutil.copytree(STAGE,DEST,dirs_exist_ok=True)
    assert inventory(DEST)==inventory(STAGE)
    subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(DEST/'verify-files.ps1')],check=True,timeout=120)
    b.write(OUT/'verification.json',dict(result='passed',distribution=str(DEST),files=len(files),bytes=sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file()),
        embedded_modules_identical=True,imports=imports,no_game_launched=True,capture_detached=True,protected_versions_unchanged=True))
    print('RELEASED',DEST,'files',len(files),flush=True)

if __name__=='__main__':main()
