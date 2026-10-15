"""Prepare an exit fix from exact current modules; install only when idle."""
import argparse,json,shutil,subprocess
from pathlib import Path
import build_remastered_11 as b
from install_11_minimap_v2 import resources
from build_11_fmv_h264 import replace
from release_remastered_11 import DEST,STAGE,ENTRY
OUT=b.ROOT/'modernization/build/remastered-1.1-surface-lifecycle'
BACK=b.ROOT/'modernization/backups/remastered-1.1-surface-lifecycle'
EXPECTED='f0baf09b41fd5f74009b55816da6bc9a37352c4c8a2756fa48f234940bdf56a2'
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def targets():return [(b.TARGET/'MagicMayhem-Remastered-1.1.exe',b.TARGET/'manifest.json','candidate'),(STAGE/ENTRY,STAGE/'release-manifest.json','release'),(DEST/ENTRY,DEST/'release-manifest.json','release')]
def native_fixture():
    # Relocate only absolute game references; Windows may reserve its low
    # address heap over the engine's addresses in a standalone test process.
    import re,pefile,capstone
    for source,dest in [(b.SRC/'surface_lifecycle.cpp','surface_lifecycle_test_hooks.cpp'),(b.ROOT/'modernization/tests/surface_lifecycle_native_test.cpp','surface_lifecycle_native_test.cpp')]:
        s=source.read_text(encoding='utf-8')
        s=re.sub(r'0x[0-9a-fA-F]+',lambda m:hex(int(m[0],16)+0x20000000) if 0x580000<=int(m[0],16)<0x700000 else m[0],s)
        s=s.replace('0xa1,0x54,0x81,0x6f,0','0xa1,0x54,0x81,0x6f,0x20')
        (OUT/dest).write_text(s,encoding='utf-8')
    pe=pefile.PE(str(b.TARGET/'runtime/Chaos-Wide169-engine.exe'))
    try:raw=bytearray(pe.get_data(0x18b3e0,0xd8))
    finally:pe.close()
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    for ins in md.disasm(raw,0x58b3e0):
        for op in ins.operands:
            if op.type==capstone.CS_OP_MEM and 0x6e0000<=op.mem.disp<0x700000:
                start=ins.address-0x58b3e0+ins.disp_offset
                raw[start:start+4]=(op.mem.disp+0x20000000).to_bytes(4,'little');break
    (OUT/'native_destroy.bin').write_bytes(raw)
def idle():
    # Refuse any live engine, including the retained shutdown scene.
    import verify_hd60_runtime as v
    k=v.configured_kernel()
    assert not any('chaos' in name and name.endswith('.exe') for _,_,name in v.processes(k)),'Game process still running; preserve debugging scene'
def build():
    OUT.mkdir(exist_ok=False)
    src=b.ROOT/'modernization/build/remastered-1.1-teammate-portrait'
    for entry,manifest,kind in targets():
        m=json.loads(manifest.read_text(encoding='utf-8'));assert b.sha(entry)==m['launcher_sha256']
        assert b.sha(entry.parent/'runtime/Chaos-Wide169-engine.exe')==m['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
        assert __import__('hashlib').sha256(resources(entry)[102]).hexdigest()==EXPECTED
    for p in src.glob('*.cpp'):shutil.copy2(p,OUT/p.name)
    for pattern in ['*.h','*.inc']:
        for p in src.glob(pattern):shutil.copy2(p,OUT/p.name)
    for name in ['surface_lifecycle.cpp','surface_registry.h']:shutil.copy2(b.SRC/name,OUT/name)
    s=(OUT/'qol_bindings.cpp').read_text(encoding='utf-8')
    s=b.replace_once(s,'extern "C" bool mm_install_window_close();','extern "C" bool mm_install_window_close();\nextern "C" bool mm_install_surface_lifecycle();')
    s=b.replace_once(s,'return install() &&','return mm_install_surface_lifecycle() && install() &&')
    (OUT/'qol_bindings.cpp').write_text(s,encoding='utf-8')
    current=resources(b.TARGET/'MagicMayhem-Remastered-1.1.exe');(OUT/'repath.dll').write_bytes(current[101])
    shutil.copy2(b.ROOT/'modernization/build/remastered-1.1-fmv-h264/launcher.cpp',OUT/'launcher.cpp')
    shutil.copy2(b.ROOT/'modernization/releases/remastered-1.1/launcher.cpp',OUT/'release_launcher.cpp')
    shutil.copy2(b.ROOT/'modernization/releases/remastered-1.1/remastered.ico',OUT/'remastered.ico')
    (OUT/'candidate.rc').write_text('101 RCDATA "repath.dll"\n102 RCDATA "qol_bindings.dll"\n')
    (OUT/'release.rc').write_text('1 ICON "remastered.ico"\n101 RCDATA "repath.dll"\n102 RCDATA "qol_bindings.dll"\n')
    shutil.copy2(b.ROOT/'modernization/tests/surface_registry_test.cpp',OUT/'surface_registry_test.cpp')
    shutil.copy2(b.ROOT/'modernization/tests/surface_lifecycle_native_test.cpp',OUT/'surface_lifecycle_native_test.cpp')
    native_fixture()
    cmd='''@echo off
call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 surface_registry_test.cpp /link /OUT:surface_registry_test.exe
if errorlevel 1 exit /b 1
surface_registry_test.exe
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 surface_lifecycle_native_test.cpp surface_lifecycle_test_hooks.cpp /link /BASE:0x10000000 /DYNAMICBASE:NO /OUT:surface_lifecycle_native_test.exe
if errorlevel 1 exit /b 1
surface_lifecycle_native_test.exe
if errorlevel 1 exit /b 1
cl /nologo /LD /O2 /EHsc /std:c++17 /W4 qol_bindings.cpp mixed_ui_fonts.cpp campaign_ui.cpp port_drag.cpp confirm_dialog.cpp qwen_highlight.cpp window_close.cpp surface_lifecycle.cpp /link /OUT:qol_bindings.dll user32.lib
if errorlevel 1 exit /b 1
rc /nologo /focandidate.res candidate.rc
if errorlevel 1 exit /b 1
rc /nologo /forelease.res release.rc
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER launcher.cpp candidate.res /link /SUBSYSTEM:WINDOWS /OUT:candidate.exe bcrypt.lib user32.lib
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER release_launcher.cpp release.res /link /SUBSYSTEM:WINDOWS /OUT:release.exe bcrypt.lib user32.lib
'''
    (OUT/'build.cmd').write_text(cmd);subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
    for name in ['candidate.exe','release.exe']:
        after=resources(OUT/name);assert after[101]==current[101] and after[102]==(OUT/'qol_bindings.dll').read_bytes()
    write(OUT/'verification.json',dict(result='passed',tests='native x86 registry deletion, duplicate ownership, repeated recreation, full capacity',module_sha256=b.sha(OUT/'qol_bindings.dll'),runtime_acceptance='pending user testing'))
    write(OUT/'before.json',[dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)) for e,m,k in targets()])
def install(metadata_key='surface_lifecycle_fix'):
    idle();rows=json.loads((OUT/'before.json').read_text());BACK.mkdir(exist_ok=False);changes=[]
    for i,r in enumerate(rows):
        entry=Path(r['entry']);manifest=Path(r['manifest']);assert b.sha(entry)==r['entry_sha256'] and b.sha(manifest)==r['manifest_sha256']
        new=OUT/('candidate.exe' if r['kind']=='candidate' else 'release.exe');m=json.loads(manifest.read_text(encoding='utf-8'))
        m['launcher_sha256']=b.sha(new)
        m[metadata_key]=json.loads((OUT/'verification.json').read_text())
        if r['kind']=='release':
            m['files'][entry.name]=b.sha(new)
            m['embedded_modules']['101']=b.sha(OUT/'repath.dll')
            m['embedded_modules']['102']=b.sha(OUT/'qol_bindings.dll')
        for j,(p,data) in enumerate([(entry,new.read_bytes()),(manifest,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode())]):
            backup=BACK/f'{i}-{j}.bak';backup.write_bytes(p.read_bytes());changes.append(dict(path=str(p),backup=str(backup),before_sha256=b.sha(p),after_sha256=__import__('hashlib').sha256(data).hexdigest(),data=data))
    write(BACK/'rollback.json',[{k:v for k,v in r.items() if k!='data'} for r in changes])
    try:
        for r in changes:replace(Path(r['path']),r['data']);assert b.sha(Path(r['path']))==r['after_sha256']
    except BaseException:
        for r in changes:replace(Path(r['path']),Path(r['backup']).read_bytes())
        raise
    print('Installed verified '+metadata_key+'; runtime acceptance pending user testing')
def rollback():
    idle();rows=json.loads((BACK/'rollback.json').read_text())
    for r in rows:assert b.sha(Path(r['path']))==r['after_sha256'] and b.sha(Path(r['backup']))==r['before_sha256']
    for r in rows:replace(Path(r['path']),Path(r['backup']).read_bytes());assert b.sha(Path(r['path']))==r['before_sha256']
    print('Rolled back exit fix')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
