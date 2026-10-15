from pathlib import Path
import hashlib,json,shutil,subprocess,pefile
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
STAGE=OUT/'runtime'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
b=json.loads((ROOT/'modernization/current-baseline.json').read_text())['latest_development']
s=json.loads((ROOT/'modernization/wide169-installed.json').read_text())
pkg=Path(s['package']); mp=pkg/'manifest.json'
assert sha(mp)==s['manifest_sha256'],'installed manifest changed'
m=json.loads(mp.read_text())
for n,h in b['files'].items():
    if n.startswith(('game/','game-wide169/')):assert sha(ROOT/n)==h,n
entry=ROOT/b['entry'];assert sha(entry)==m['launcher_sha256']
assert sha(ROOT/'game-wide169/Chaos-Wide169-engine.exe')==m['engine_sha256']
if STAGE.exists():raise RuntimeError('Release staging already exists')
STAGE.mkdir()
excluded=[];changed=[]
mutable={'CFG/prefs.cfg','ddraw.ini','modernization/config/qol-hotkeys.json'}
for n,h in m['files'].items():
    p=ROOT/'game-wide169'/n
    if n.startswith(('Save/','ss/','modernization/logs/')) or n in {'Readme.txt','Readme.wri','Uninst.isu','wide169-lab.json'}:
        excluded.append(n);continue
    assert p.is_file() and not p.is_symlink(),n
    actual=sha(p)
    if actual!=h:
        assert n in mutable or n.startswith(('AI/','CFG/Encrypted/')), 'Runtime differs from package: '+n
        changed.append({'path':n,'package_sha256':h,'installed_sha256':actual})
    if n not in mutable:
        p=pkg/'runtime'/n;assert sha(p)==h,n
    dest=STAGE/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
for n in ['Save','modernization/config']:(STAGE/n).mkdir(parents=True,exist_ok=True)
# Preserve historical community documentation separately from the new release README.
(STAGE/'Documentation').mkdir()
for n in ['Readme.txt','Readme.wri']:shutil.copy2(ROOT/'game-wide169'/n,STAGE/'Documentation'/('Community-'+n))
pe=pefile.PE(str(entry));modules={}
for typ in pe.DIRECTORY_ENTRY_RESOURCE.entries:
    if typ.id!=10:continue
    for item in typ.directory.entries:
        d=item.directory.entries[0].data.struct
        raw=pe.get_data(d.OffsetToData,d.Size)
        name={101:'wide169.dll',102:'qol_bindings.dll'}[item.id]
        (OUT/name).write_bytes(raw);modules[str(item.id)]=hashlib.sha256(raw).hexdigest()
assert modules['101']==m['path_review']['repath_sha256']
assert modules['102']==m['qol_refresh']['qol_sha256']
source=(ROOT/'modernization/build/terrain-diagonal-v1/launcher.cpp').read_text()
old='std::wstring game=parent(parent(module))+L"\\\\game-wide169";'
assert source.count(old)==1
source=source.replace(old,'std::wstring game=parent(module);')
source=source.replace('0a18ddae17025d16b44197b4eddca09685a63c1a8dbac130d9c3e1e5d7068391',sha(STAGE/'terrain_diagonal.dll'))
# Logs are optional developer diagnostics; retain module bytes but ship no trace directories.
start=source.index('    std::wstring log=')
end=source.index('    STARTUPINFOW startup=',start)
source=source[:start]+source[end:]
source=source.replace('Trial modules','Game modules').replace('QoL trial','QoL module').replace('Terrain candidate module','Terrain module')
(OUT/'launcher.cpp').write_text(source,encoding='utf-8')
(OUT/'release.rc').write_text('101 RCDATA "wide169.dll"\n102 RCDATA "qol_bindings.dll"\n')
engine=sha(STAGE/'Chaos-Wide169-engine.exe')
cmd='@echo off\ncall "C:\\Program Files\\Microsoft Visual Studio\\18\\Community\\VC\\Auxiliary\\Build\\vcvarsall.bat" x86 >nul\nif errorlevel 1 exit /b 1\nrc /nologo /forelease.res release.rc\nif errorlevel 1 exit /b 1\ncl /nologo /O2 /EHsc /std:c++17 /W4 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER /DMM_EXPECTED_ENGINE_SHA=L\\"'+engine+'\\" launcher.cpp release.res /Forelease-launcher.obj /link /SUBSYSTEM:WINDOWS /OUT:"runtime\\MagicMayhem-Remastered.exe" bcrypt.lib user32.lib\nexit /b %errorlevel%\n'
(OUT/'build.cmd').write_text(cmd)
write(OUT/'provenance.json',{'source_entry':str(entry),'source_sha256':sha(entry),'package':str(pkg),'package_manifest_sha256':sha(mp),'embedded_module_sha256':modules,'excluded':excluded,'mutable_differences':changed,'validation':'Static file integrity; gameplay acceptance pending user testing'})
print(json.dumps({'staged_files':sum(1 for p in STAGE.rglob('*') if p.is_file()),'modules':modules,'mutable_differences':changed},indent=2))


