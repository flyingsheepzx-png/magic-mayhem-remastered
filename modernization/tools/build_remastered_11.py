"""Build/install the v38-derived 1.1 P1 candidate; never launch gameplay."""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess
import pefile
ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'modernization/build/remastered-1.1-p1'
TARGET=ROOT/'modernization/playtests/remastered-1.1-p1'
BASE=ROOT/'modernization/build/wide169/package-v38-png-assets'
HD=ROOT/'modernization/playtests/mixed-ui-v4'
ANCESTOR=ROOT/'modernization/backups/wide169/fmv-center-1790688961355333800/Chaos-Wide169-engine.exe'
SRC=ROOT/'modernization/runtime/hd11'
VC=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat')
MSBUILD=Path('C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def inventory(root):
    result={}
    for directory,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[d for d in dirs if not (Path(directory)/d).is_symlink()]
        for name in files:
            f=Path(directory)/name;result[f.relative_to(root).as_posix()]=sha(f)
    return result

def replace_once(text,old,new):
    if text.count(old)!=1: raise RuntimeError('Unexpected source pattern: '+old[:90])
    return text.replace(old,new,1)

def sources():
    m=json.loads((BASE/'manifest.json').read_text(encoding='utf-8')); s=ROOT/'modernization/runtime/wide169'
    for name,digest in m['path_review']['source_sha256'].items():
        if sha(s/name)!=digest: raise RuntimeError('Unverified latest source '+name)
    if sha(s/'qol_bindings.cpp')!=m['qol_refresh']['source_sha256']:raise RuntimeError('Unverified latest QoL source')
    for n in ['repath_multiunit_trial.cpp','clock_trial.cpp','logic_time_trial.cpp','game_time_trial.cpp','command_index.h','ui_layout.h']:shutil.copy2(s/n,BUILD/n)
    render=(s/'render_replay_trial.cpp').read_text(encoding='utf-8')
    render=replace_once(render,'(candidate_width==1280 && candidate_height==720);','(candidate_width==1280 && candidate_height==720) ||\n                       (candidate_width==2560 && candidate_height==1440);')
    render=replace_once(render,'    bool eligible=replay_enabled',
        '    bool mixed=candidate_width==2560 && candidate_height==1440 &&\n               mm_hd_current().mode==MM_HD_BATTLE;\n    int storage_width=mixed?1280:candidate_width,storage_height=mixed?720:candidate_height;\n    bool eligible=replay_enabled')
    render=replace_once(render,'known_surface && candidate_width<=kMaxWidth && candidate_height<=kMaxHeight &&',
        'known_surface && storage_width<=kMaxWidth && storage_height<=kMaxHeight &&')
    render=replace_once(render,'frame_width=candidate_width;frame_height=candidate_height;',
        'frame_width=storage_width;frame_height=storage_height;')
    render=render.replace("// engine's verified 1120x840 surface; storage is bounded by that maximum.", '// battle source area; HD primary stride does not enlarge cached battle pixels.')
    render='#include "layout_context.h"\n'+render
    render=replace_once(render,'int w=g(0x6a49f0),h=g(0x6a49f4),count=g(0x6a2dd0+0x1518);','MmHdLayoutContext context=mm_hd_current();\n    int w=context.mode==MM_HD_BATTLE?1280:g(0x6a49f0);\n    int h=context.mode==MM_HD_BATTLE?720:g(0x6a49f4),count=g(0x6a2dd0+0x1518);')
    (BUILD/'render_replay_trial.cpp').write_text(render,encoding='utf-8')
    q=(s/'qol_bindings.cpp').read_text(encoding='utf-8'); old=(ROOT/'modernization/build/mixed-ui-v4-runtime/qol_bindings.cpp').read_text(encoding='utf-8')
    q='#include "layout_context.h"\n#include <utility>\n'+q
    q=replace_once(q,'if(width!=1280 || height!=720)return;','if(!((width==1280 && height==720) || (width==2560 && height==1440)))return;')
    q=replace_once(q,'int x=r->right-18,y=r->bottom-23;\n                if(x<0 || y<0 || x+14>=width || y+18>=height)continue;','int scale=battle?1:mm_hd_current().font_scale;\n                int x=r->right-18*scale,y=r->bottom-23*scale;\n                if(x<0 || y<0 || x+14*scale>=width || y+18*scale>=height)continue;')
    q=replace_once(q,'*reinterpret_cast<unsigned short*>(pixels+(y+yy)*pitch+(x+xx)*2)=colour;','for(int sy=0;sy<scale;sy++)for(int sx=0;sx<scale;sx++)\n                        *reinterpret_cast<unsigned short*>(pixels+(y+yy*scale+sy)*pitch+(x+xx*scale+sx)*2)=colour;')
    start=old.index('// v4-only Grimoire diagnostic:');end=old.index('bool install() {',start)
    q=replace_once(q,'bool install() {',old[start:end]+'bool install() {')
    checks='''    constexpr unsigned char hd_page[]={0x81,0xec,0x34,0x02,0x00,0x00,0x53};
    constexpr unsigned char hd_tab[]={0x83,0xec,0x14,0x53,0x55,0x56};
    if(memcmp((void*)0x4c5520,hd_page,7) || memcmp((void*)0x4cb5a0,hd_tab,6))return false;
'''
    q=replace_once(q,'bool install() {','bool install() {\n'+checks)
    q=replace_once(q,'*reinterpret_cast<int*>(site)=address==0x5519da?800:600;','*reinterpret_cast<int*>(site)=address==0x5519da?1760:1320;')
    start=old.index('    for(auto entry:{std::pair<unsigned,size_t>{0x4c5520,7}');end=old.index('    return true;',start)
    q=replace_once(q,'    return true;\n}\n}\nBOOL WINAPI DllMain',old[start:end]+'    return true;\n}\n}\nextern "C" bool mm_install_mixed_fonts();\nBOOL WINAPI DllMain')
    q=replace_once(q,'return install()?TRUE:FALSE;','return install() && mm_install_mixed_fonts()?TRUE:FALSE;')
    import sys
    sys.path.insert(0,str(SRC))
    from realm_adapter import adapt
    q=adapt(q)
    (BUILD/'qol_bindings.cpp').write_text(q,encoding='utf-8')
    for n in ['layout_context.h','mixed_ui_fonts.cpp','ui_geometry.h']:shutil.copy2(SRC/n,BUILD/n)
    return m

def engine():
    a=ANCESTOR.read_bytes(); b=(HD/'game-wide169/Chaos-Wide169-engine.exe').read_bytes(); c=(BASE/'runtime/Chaos-Wide169-engine.exe').read_bytes()
    assert hashlib.sha256(a).hexdigest()=='1d2df6135238dec69f6ec74280440a06b43c66353c886f42633f4143d710b16f'
    assert hashlib.sha256(b).hexdigest()=='3eda4a37079e6c4fb09dfc1b01760afa0bf6979d82dd479a56631f5ea96f056d'
    assert hashlib.sha256(c).hexdigest()=='43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d'
    assert len(a)==len(b)==len(c)
    out=bytearray(c);changes=[]
    for i,(x,y,z) in enumerate(zip(a,b,c)):
        if x!=y:
            if z not in (x,y):raise RuntimeError('Engine merge conflict '+hex(i))
            out[i]=y;changes.append(i)
    assert all(out[i]==z for i,(x,y,z) in enumerate(zip(a,b,c)) if z!=x and x==y)
    p=BUILD/'Chaos-Wide169-engine.exe';p.write_bytes(out)
    write(BUILD/'engine-merge.json',dict(ancestor_sha256=hashlib.sha256(a).hexdigest(),hd_sha256=hashlib.sha256(b).hexdigest(),v38_sha256=hashlib.sha256(c).hexdigest(),sha256=sha(p),hd_changed_bytes=len(changes),latest_changed_bytes=sum(x!=z for x,z in zip(a,c)),conflicts=0,offsets=changes))
    return sha(p)

def build():
    if BUILD.exists() or TARGET.exists():raise RuntimeError('Preserve existing build/candidate; choose a new checkpoint')
    state=json.loads((ROOT/'modernization/wide169-installed.json').read_text(encoding='utf-8'))
    assert Path(state['package'])==BASE and sha(BASE/'manifest.json')==state['manifest_sha256']
    manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'));assert inventory(BASE/'runtime')==manifest['files']
    hm=json.loads((HD/'manifest.json').read_text(encoding='utf-8'));assert all(sha(HD/n)==h for n,h in hm['files'].items())
    BUILD.mkdir(parents=True);sources();digest=engine()
    # The new merged engine must be accepted by its production PNG dependency.
    shutil.copy2(SRC/'png_assets.cpp',BUILD/'png_assets.cpp')
    (BUILD/'build-png.cmd').write_text('@echo off\ncall "'+str(VC)+'" x86 >nul\nif errorlevel 1 exit /b 1\ncl /nologo /LD /MT /O2 /EHsc /std:c++17 /W4 png_assets.cpp /link /OUT:png_assets.dll ole32.lib windowscodecs.lib\n',encoding='utf-8')
    subprocess.run(['cmd.exe','/c','build-png.cmd'],cwd=BUILD,check=True)
    launcher=(ROOT/'modernization/releases/remastered-1.0/launcher.cpp').read_text(encoding='utf-8')
    launcher=replace_once(launcher,'206c645ec6f3e76bf548dedd9cc874f101dba1fc37d328f71343d8a3d4fa8839',sha(BUILD/'png_assets.dll'))
    launcher=replace_once(launcher,'#define MM_EXPECTED_ENGINE_SHA L"43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d"','#define MM_EXPECTED_ENGINE_SHA L"'+digest+'"')
    launcher=replace_once(launcher,'    if (!CreateProcessW(','    SetEnvironmentVariableW(L"MM_PROBE_MIXED_RENDER",L"1");\n    SetEnvironmentVariableW(L"MM_PROBE_MIXED_FONTS",L"1");\n    SetEnvironmentVariableW(L"MM_PROBE_BATTLE_SHARPEN",L"0");\n    if (!CreateProcessW(')
    (BUILD/'launcher.cpp').write_text(launcher,encoding='utf-8')
    (BUILD/'combined.rc').write_text('101 RCDATA "repath.dll"\n102 RCDATA "qol_bindings.dll"\n',encoding='ascii')
    cmd='''@echo off
call "{vc}" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /LD /O2 /EHsc /std:c++17 /W4 /DMM_COMBINED /DMM_ALL_IN_ONE repath_multiunit_trial.cpp render_replay_trial.cpp clock_trial.cpp logic_time_trial.cpp game_time_trial.cpp /link /OUT:repath.dll /MAP:repath.map
if errorlevel 1 exit /b 1
cl /nologo /LD /O2 /EHsc /std:c++17 /W4 qol_bindings.cpp mixed_ui_fonts.cpp /link /OUT:qol_bindings.dll /MAP:qol_bindings.map user32.lib
if errorlevel 1 exit /b 1
rc /nologo /focandidate.res combined.rc
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 /W4 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER launcher.cpp candidate.res /link /SUBSYSTEM:WINDOWS /OUT:MagicMayhem-Remastered-1.1.exe bcrypt.lib user32.lib
'''.format(vc=VC)
    (BUILD/'build.cmd').write_text(cmd);subprocess.run(['cmd.exe','/c','build.cmd'],cwd=BUILD,check=True)
    wrapper()
    write(BUILD/'build-provenance.json',dict(base_manifest_sha256=sha(BASE/'manifest.json'),hd_manifest_sha256=sha(HD/'manifest.json'),v38_source_hashes=manifest['path_review']['source_sha256'],qol_source_sha256=manifest['qol_refresh']['source_sha256'],sources={f.name:sha(f) for f in BUILD.iterdir() if f.suffix in ('.cpp','.h')},runtime_acceptance='pending user testing'))
    print('Build complete:',BUILD)

def wrapper():
    ws=BUILD/'wrapper'
    if not ws.exists():shutil.copytree(ROOT/'modernization/build/cnc-ddraw-src',ws,ignore=shutil.ignore_patterns('.git','.vs','bin','obj','Debug','Release'))
    shutil.copy2(SRC/'layout_context.h',ws/'src/layout_context.h')
    h=(ROOT/'modernization/wrapper-probe/mm_mixed.h').read_text(encoding='utf-8');h='#include "layout_context.h"\n'+h
    a=h.index('#define MM_MIXED_PLAYTEST_V4_PATH ');end=h.index('\n',a)
    hp=str(TARGET/'runtime/Chaos-Wide169-engine.exe').replace('\\','\\\\')
    h=h[:end]+('\n#define MM_MIXED_HD11_PATH "'+hp+'"')+h[end:]
    h=replace_once(h,'_stricmp(path, MM_MIXED_PLAYTEST_V4_PATH) == 0)','_stricmp(path, MM_MIXED_PLAYTEST_V4_PATH) == 0 ||\n             _stricmp(path, MM_MIXED_HD11_PATH) == 0)')
    a=h.index('static BOOL mm_mixed_readable');end=h.index('IDirectDrawSurfaceImpl* mm_mixed_present',a)
    h=h[:a]+'''static BOOL mm_mixed_is_battle(IDirectDrawSurfaceImpl* primary)
{
    (void)primary;
    return mm_hd_current().mode==MM_HD_BATTLE;
}

'''+h[end:]
    h=replace_once(h,'result.x /= 2;\n        result.y /= 2;','result=mm_hd_input(mm_hd_current(),x,y);')
    (ws/'src/mm_mixed.h').write_text(h,encoding='utf-8')
    # Production identity is portable and refuses unknown engine versions.
    import portable_11_wrapper as portable
    portable.apply(ws)
    subprocess.run([str(MSBUILD),'cnc-ddraw.vcxproj','/p:Configuration=Release','/p:Platform=Win32','/m','/v:minimal'],cwd=ws,check=True)

def install():
    if TARGET.exists():raise RuntimeError('Do not overwrite existing candidate or its saves')
    prov=json.loads((BUILD/'build-provenance.json').read_text(encoding='utf-8'));assert sha(BASE/'manifest.json')==prov['base_manifest_sha256']
    assert inventory(BASE/'runtime')==json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))['files']
    guard={str(p):sha(p) for p in [ROOT/'game/Chaos-Wide169-Trial.exe',ROOT/'game-wide169/Chaos-Wide169-engine.exe',ROOT/'modernization/current-baseline.json',ROOT/'modernization/wide169-installed.json',Path('D:/Games/Magic&Mayham_Remastered_1.0/MagicMayhem-Remastered.exe')]}
    backup=ROOT/'modernization/backups/remastered-1.1-p1';backup.mkdir(parents=True,exist_ok=False)
    for n in ['current-baseline.json','wide169-installed.json']:shutil.copy2(ROOT/'modernization'/n,backup/n)
    write(backup/'protected.json',guard)
    TARGET.mkdir();runtime=TARGET/'runtime';shutil.copytree(BASE/'runtime',runtime);overlays=[]
    for directory,dirs,files in os.walk(HD/'game-wide169',followlinks=False):
        dirs[:]=[d for d in dirs if d not in ('modernization','Save','ss','AI','CFG','FMV')]
        for n in files:
            f=Path(directory)/n;rel=f.relative_to(HD/'game-wide169')
            if rel.parts[0] not in ('Interface','Sprites') and str(rel)!='chaos95.dll':continue
            target=runtime/rel
            if not target.exists() or sha(target)!=sha(f):
                before=sha(target) if target.exists() else None;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
                overlays.append(dict(path=rel.as_posix(),v38_sha256=before,sha256=sha(target)))
    production=ROOT/'modernization/assets/hd/seedvr2-ui-1.1/plan.json'
    art=json.loads(production.read_text(encoding='utf-8'))
    if art['status']!='installed':raise RuntimeError('Finish approved SeedVR2 production; retired Qwen packs are not a rebuild source')
    icon_meta=next(a for a in art['assets'] if a['path']=='Sprites/port-icons.spr')
    icon_derivative=Path(icon_meta['output'])
    if sha(icon_derivative)!=icon_meta['sha256']:raise RuntimeError('Unknown SeedVR2 page icon derivative')
    shutil.copy2(icon_derivative,runtime/'Sprites/port-icons.spr')
    cfg=runtime/'Interface/Grimoire/Grimoire.cfg';latest=(BASE/'runtime/Interface/Grimoire/Grimoire.cfg').read_bytes();hd=cfg.read_bytes()
    for key,value in re.findall(rb'(?m)^\s*(800x600_\d+R[XY])\s*=\s*(-?\d+)',latest):
        hd,count=re.subn(rb'(?m)^(\s*'+re.escape(key)+rb'\s*=\s*)-?\d+',lambda m:m[1]+str(int(value)*2).encode(),hd);assert count==1
    cfg.write_bytes(hd)
    # v21's corrected clasp silhouette supersedes the older HD 27x116 source.
    from spr_assets import read_spr,decode
    from stage_mixed_ui_v3_sprites import encode
    from PIL import Image,ImageChops
    import struct
    rel=Path('Interface/Grimoire/800x600/icons.spr')
    pal,frames=read_spr(runtime/rel);source_pal,source_frames=read_spr(BASE/'runtime'/rel)
    payloads=[]
    for frame in frames:
        if frame['index'] not in (0,1):payloads.append(frame['data']);continue
        source=source_frames[frame['index']]
        assert (source['width'],source['height'])==(32,139)
        image=decode(source_pal,source).resize((64,278),Image.Resampling.LANCZOS)
        image.putalpha(decode(source_pal,source).getchannel('A').resize((64,278),Image.Resampling.NEAREST))
        payloads.append(encode(source,image))
    raw=(runtime/rel).read_bytes();output=bytearray(raw[:24]);offset=0
    for payload in payloads:output.extend(struct.pack('<I',offset));offset+=len(payload)
    for payload in payloads:output.extend(payload)
    struct.pack_into('<I',output,4,len(output));(runtime/rel).write_bytes(output)
    new_pal,new_frames=read_spr(runtime/rel)
    assert [(f['width'],f['height']) for f in new_frames[:2]]==[(64,278)]*2
    assert all(x['data']==y['data'] for x,y in zip(frames[2:],new_frames[2:]))
    # Historical candidate supplies geometry/code only. Replace every selected
    # UI media file with the approved, hash-bound SeedVR2 production output.
    for asset in art['assets']:
        source=Path(asset['output'])
        if asset['status']!='installed' or sha(source)!=asset['sha256']:raise RuntimeError('Incomplete SeedVR2 asset '+asset['path'])
        shutil.copy2(source,runtime/asset['path'])
    for source,target in [(BUILD/'png_assets.dll',runtime/'png_assets.dll'),(BUILD/'Chaos-Wide169-engine.exe',runtime/'Chaos-Wide169-engine.exe'),(BUILD/'wrapper/bin/Release/ddraw.dll',runtime/'ddraw.dll'),(BUILD/'MagicMayhem-Remastered-1.1.exe',TARGET/'MagicMayhem-Remastered-1.1.exe')]:shutil.copy2(source,target)
    ini=(HD/'game-wide169/ddraw.ini').read_bytes()
    for key,value in [(b'width',b'2560'),(b'height',b'1440'),(b'd3d9_filter',b'0'),(b'border',b'false'),(b'renderer',b'direct3d9'),(b'resizable',b'false')]:
        ini,count=re.subn(rb'(?m)^'+key+rb'=.*$',key+b'='+value,ini,count=1);assert count==1
    (runtime/'ddraw.ini').write_bytes(ini)
    for rel in ['Save','modernization/config']:
        source=ROOT/'game-wide169'/rel
        if source.exists():shutil.copytree(source,runtime/rel,dirs_exist_ok=True)
    prefs=(ROOT/'game-wide169/CFG/prefs.cfg').read_bytes();assert re.search(rb'MaxFramesPerSec\s*=\s*30',prefs);(runtime/'CFG/prefs.cfg').write_bytes(prefs)
    (TARGET/'Run-1.1.cmd').write_text('@echo off\ncd /d "%~dp0"\nstart "" "MagicMayhem-Remastered-1.1.exe"\n',encoding='ascii')
    (TARGET/'README-TEST.txt').write_text('Magic & Mayhem 1.1 — P1 高清开发候选\n\n运行 MagicMayhem-Remastered-1.1.exe，启动前退出其他游戏实例。\n独立 UI：1920×1440 原生内容，居中于 2560×1440。\n局内：1280×720 场景/HUD，整体放大 2×；滤镜关闭。\n保留 v38 寻路、半透明及 QoL；存档和设置均为独立副本。\n本阶段重点反馈菜单、设置、读档/存档、进入战斗和返回 UI。\n其他高清页面沿用旧候选适配成果，尚待逐页验收和素材优化。\n运行接受状态等待你的试玩。\n回到 1.0：退出本候选，运行原来的 1.0 入口。\n',encoding='utf-8-sig')
    write(TARGET/'manifest.json',dict(version='1.1',checkpoint='P1',parent_package=str(BASE),engine_sha256=sha(runtime/'Chaos-Wide169-engine.exe'),files=inventory(runtime),launcher_sha256=sha(TARGET/'MagicMayhem-Remastered-1.1.exe'),native_ui=[1920,1440],ui_origin=[320,0],native_battle=[1280,720],output=[2560,1440],logic_preference=30,filter='disabled',validation='build and offline only; pending user testing',backup=str(backup)))
    write(BUILD/'asset-overlay.json',overlays);assert all(sha(Path(p))==h for p,h in guard.items());verify();print('Installed isolated candidate:',TARGET)

def verify():
    m=json.loads((TARGET/'manifest.json').read_text(encoding='utf-8'));actual=inventory(TARGET/'runtime')
    mutable=lambda n:n.startswith(('Save/','ss/','CFG/Encrypted/','modernization/logs/')) or n in ('AI/EXPERIEN.DAT','AI/Brain.dat','CFG/prefs.cfg','ddraw.ini','modernization/config/qol-hotkeys.json','fmv-h264-events.jsonl')
    changed=[n for n,h in m['files'].items() if not mutable(n) and actual.get(n)!=h]
    extra=[n for n in actual if n not in m['files'] and not mutable(n)]
    if changed or extra:raise RuntimeError('Candidate integrity mismatch: '+str(changed+extra))
    assert sha(TARGET/'MagicMayhem-Remastered-1.1.exe')==m['launcher_sha256']
    for p,h in json.loads((ROOT/'modernization/backups/remastered-1.1-p1/protected.json').read_text(encoding='utf-8')).items():assert sha(Path(p))==h
    assert not list((TARGET/'runtime').rglob('*.bmp'));print('Integrity verified:',len(m['files']),'runtime files; protected v38/1.0 unchanged')

def rollback():
    from verify_hd60_runtime import configured_kernel,processes
    if any(name.startswith('chaos') for _,_,name in processes(configured_kernel())):
        raise RuntimeError('Close the game before disabling the candidate')
    runtime=TARGET/'runtime';parked=ROOT/'modernization/backups/remastered-1.1-p1/user-runtime'
    assert runtime.resolve().parent==TARGET.resolve() and parked.resolve().parent==(ROOT/'modernization/backups/remastered-1.1-p1').resolve()
    if parked.exists():raise RuntimeError('Existing preserved runtime; do not overwrite')
    runtime.rename(parked);print('Candidate disabled; saves/configuration preserved at',parked)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','install','verify','rollback']);args=parser.parse_args();globals()[args.action]()
