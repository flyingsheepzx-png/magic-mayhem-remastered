"""Prepare item1 from current danger refresh and transition-v6 sources."""
import json,shutil,subprocess
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
OUT=b.ROOT/'modernization/build/remastered-1.1-options-resolution-v2'
def main():
 source=b.ROOT/'modernization/build/remastered-1.1-danger-refresh'
 current=resources(base.DEST/base.ENTRY);assert current==resources(source/'candidate.exe')
 rows=[]
 for e,m,k in base.targets():
  manifest=json.loads(m.read_text(encoding='utf-8'))
  assert b.sha(e)==manifest['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==manifest['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m),wrapper_sha256=b.sha(e.parent/'runtime/ddraw.dll')))
 OUT.mkdir(exist_ok=False);base.write(OUT/'before.json',rows)
 for p in source.iterdir():
  if p.suffix in ['.cpp','.h','.inc','.cmd','.rc','.ico','.bin']:shutil.copy2(p,OUT/p.name)
 for i,name in [(101,'repath.dll'),(103,'ai_diagnostics.dll')]: (OUT/name).write_bytes(current[i])
 shutil.copy2(b.SRC/'options_resolution.cpp',OUT/'options_resolution.cpp')
 p=OUT/'qol_bindings.cpp';s=p.read_text(encoding='utf-8')
 s=b.replace_once(s,'extern "C" bool mm_install_ai_danger_refresh();','extern "C" bool mm_install_ai_danger_refresh();\nextern "C" bool mm_install_options_resolution();')
 s=b.replace_once(s,'return mm_install_ai_danger_refresh() &&','return mm_install_options_resolution() && mm_install_ai_danger_refresh() &&');p.write_text(s,encoding='utf-8')
 p=OUT/'build.cmd';p.write_text(b.replace_once(p.read_text(),'ai_danger_refresh.cpp /link','ai_danger_refresh.cpp options_resolution.cpp /link'))
 original=b.ROOT/'modernization/build/remastered-1.1-transition-present-v6/wrapper'
 assert b.sha(original/'bin/Release/ddraw.dll')==rows[0]['wrapper_sha256']
 ws=OUT/'wrapper';shutil.copytree(original,ws,ignore=shutil.ignore_patterns('bin','obj','Debug','Release','.vs'))
 shutil.copy2(b.SRC/'display_resolution.h',ws/'src/display_resolution.h')
 p=ws/'src/wndproc.c';s=p.read_text(encoding='utf-8-sig');s=b.replace_once(s,'LRESULT CALLBACK fake_WndProc','#include "display_resolution.h"\n\nLRESULT CALLBACK fake_WndProc')
 s=b.replace_once(s,'    if ((mm_background_enabled()','    if(uMsg==mm_display_message() && mm_mixed_enabled())return mm_display_apply_resolution(wParam,lParam);\n    if ((mm_background_enabled()');p.write_text(s)
 # Config uses a load-only header because dd_SetDisplayMode belongs to dd.c.
 h=(b.SRC/'display_resolution.h').read_text();h=h[:h.index('static UINT mm_display_message')]+ '\n#endif\n'
 (ws/'src/display_resolution_load.h').write_text(h)
 p=ws/'src/config.c';s=p.read_text(encoding='utf-8-sig');s=b.replace_once(s,'void cfg_load()','#include "display_resolution_load.h"\n\nvoid cfg_load()')
 # Load override at end of cfg_load, after per-game preferences are parsed.
 start=s.index('void cfg_load()');end=s.index('\n}',start)
 s=s[:end]+'\n    mm_display_load_resolution();'+s[end:];p.write_text(s)
 p=ws/'src/dd.c';s=p.read_text(encoding='utf-8-sig');s=b.replace_once(s,'#include "config.h"','#include "config.h"\n#include "display_resolution_load.h"')
 s=b.replace_once(s,'if (!zooming || g_config.fullscreen)','if ((!zooming || g_config.fullscreen) && !mm_display_width())');p.write_text(s)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
 for name in ['candidate.exe','release.exe']:
  r=resources(OUT/name);assert r[101]==current[101] and r[103]==current[103]
 subprocess.run([str(b.MSBUILD),'cnc-ddraw.vcxproj','/p:Configuration=Release','/p:Platform=Win32','/m','/v:minimal'],cwd=ws,check=True)
 base.write(OUT/'preparation.json',dict(status='compiled; verification and labels pending',launcher_sha256=b.sha(OUT/'release.exe'),wrapper_sha256=b.sha(ws/'bin/Release/ddraw.dll'),preserved_modules=[101,103],source=str(source)))
if __name__=='__main__':main()
