from pathlib import Path
import hashlib,json,pefile
R=Path(__file__).resolve().parent;S=R/'runtime'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((R/'provenance.json').read_text())
source=Path(p['source_entry']);src=pefile.PE(str(source));exe=S/'MagicMayhem-Remastered.exe';dst=pefile.PE(str(exe))
def resources(pe):
 result={}
 for t in pe.DIRECTORY_ENTRY_RESOURCE.entries:
  if t.id==10:
   for e in t.directory.entries:
    d=e.directory.entries[0].data.struct;result[str(e.id)]=hashlib.sha256(pe.get_data(d.OffsetToData,d.Size)).hexdigest()
 return result
assert resources(src)==resources(dst)==p['embedded_module_sha256']
raw=exe.read_bytes();engine=sha(S/'Chaos-Wide169-engine.exe');terrain=sha(S/'terrain_diagonal.dll')
assert engine.encode('utf-16le') in raw and terrain.encode('utf-16le') in raw
assert 'game-wide169'.encode('utf-16le') not in raw
assert str(source.parents[1]).encode('utf-16le') not in raw
assert 'MaxFramesPerSec=30' in (S/'CFG/prefs.cfg').read_text()
assert not list((S/'Save').iterdir())
assert not any(x.is_symlink() or x.is_junction() for x in S.rglob('*'))
# All shipped local imports resolve to the release or the Windows platform.
osdll={'kernel32.dll','user32.dll','gdi32.dll','advapi32.dll','shell32.dll','ole32.dll','oleaut32.dll','comdlg32.dll','comctl32.dll','winmm.dll','version.dll','ws2_32.dll','wsock32.dll','ntdll.dll','bcrypt.dll','crypt32.dll','winspool.drv','msvcrt.dll','shlwapi.dll','msacm32.dll','avifil32.dll','vfw32.dll','imm32.dll','ddraw.dll','dsound.dll','dinput.dll','dinput8.dll','d3d9.dll','opengl32.dll','wininet.dll','msimg32.dll','rpcrt4.dll','psapi.dll','secur32.dll','dwmapi.dll','setupapi.dll','hid.dll','cfgmgr32.dll','ucrtbase.dll','wintrust.dll','iphlpapi.dll','mpr.dll','dbghelp.dll','urlmon.dll','msvfw32.dll','msacm32.drv','lz32.dll','windowscodecs.dll','shcore.dll','uxtheme.dll'}
imports={};unknown=[]
for f in list(S.glob('*.exe'))+list(S.glob('*.dll'))+list(R.glob('*.dll')):
 pe=pefile.PE(str(f));names=[]
 for typ in ('DIRECTORY_ENTRY_IMPORT','DIRECTORY_ENTRY_DELAY_IMPORT'):
  for e in getattr(pe,typ,[]):
   n=e.dll.decode().lower();names.append(n)
   if not (S/n).exists() and n not in osdll and not n.startswith(('api-ms-','ext-ms-')):unknown.append((f.name,n))
 imports[f.name]=sorted(set(names))
assert not unknown,unknown
files={x.relative_to(S).as_posix():sha(x) for x in sorted(S.rglob('*')) if x.is_file() and x.name!='release-manifest.json'}
manifest={'version':'1.0','date':'2026-09-30','source_entry_sha256':p['source_sha256'],'source_package_manifest_sha256':p['package_manifest_sha256'],'launcher_sha256':sha(exe),'engine_sha256':engine,'terrain_sha256':terrain,'embedded_modules':resources(dst),'native_battle_canvas':[1280,720],'default_output':[2560,1440],'MaxFramesPerSec':30,'validation':'Build and static integrity passed; gameplay pending user','files':files}
(S/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(R/'verification.json').write_text(json.dumps({'status':'passed','files':len(files),'bytes':sum(x.stat().st_size for x in S.rglob('*') if x.is_file()),'imports':imports,'embedded_modules_identical':True,'source_launcher_unchanged':sha(source)==p['source_sha256'],'no_game_launched':True},indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2))

