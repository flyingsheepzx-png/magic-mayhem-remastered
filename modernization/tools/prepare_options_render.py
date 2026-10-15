"""Fourth sequential setting: independently capped Direct3D9 presentations."""
import json,shutil,subprocess,re,pefile
import prepare_options_speed as p
b=p.b;base=p.base;resources=p.p.resources
SOURCE=p.OUT
OUT=b.ROOT/'modernization/build/remastered-1.1-options-render-v1'
BACK=b.ROOT/'modernization/backups/remastered-1.1-options-render-v1'
SCREEN=p.SCREEN
FULL_NATIVE='8b46638b482885c97e0b8b50248b48208b0c91eb0233c98b512d83ea0483fa027f288b482885c97e0b8b48248b50208b0c8aeb0233c98b492d83e904790cc705f5e66d0000000000eb4a8b482885c97e0b8b50248b48208b0c91eb0233c98b512d83ea0483fa027e0cc705f5e66d0002000000eb1f8b482885c97e0b8b48248b50208b048aeb0233c08b402d83e804a3f5e66d00'
def build():
 current=resources(base.DEST/base.ENTRY);assert current==resources(SOURCE/'release.exe')
 rows=[]
 for e,m,k in base.targets():
  d=json.loads(m.read_text(encoding='utf-8'));assert b.sha(e)==d['launcher_sha256'] and resources(e)==current
  assert b.sha(e.parent/'runtime/ddraw.dll')==b.sha(SOURCE/'wrapper/bin/Release/ddraw.dll')
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==d['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m),wrapper_sha256=b.sha(e.parent/'runtime/ddraw.dll')))
 pe=pefile.PE(str(base.DEST/'runtime/Chaos-Wide169-engine.exe'));assert pe.get_data(0xa9949,0x94).hex()==FULL_NATIVE
 OUT.mkdir(exist_ok=False);base.write(OUT/'before.json',rows)
 for f in SOURCE.iterdir():
  if f.suffix in ['.cpp','.h','.inc','.cmd','.rc','.ico','.bin','.dll']:shutil.copy2(f,OUT/f.name)
 source=(b.SRC/'options_render.cpp').read_text();source=source.replace('const BYTE begin[]={0x8b,0x46,0x63,0x8b,0x48,0x28};','const BYTE begin[]={'+','.join('0x'+FULL_NATIVE[n:n+2] for n in range(0,len(FULL_NATIVE),2))+'};').replace('memcmp((void*)0x4a9949,begin,6)','memcmp((void*)0x4a9949,begin,sizeof begin)');(OUT/'options_render.cpp').write_text(source)
 f=OUT/'qol_bindings.cpp';s=f.read_text(encoding='utf-8');s=b.replace_once(s,'extern "C" bool mm_install_options_speed();','extern "C" bool mm_install_options_speed();\nextern "C" bool mm_install_options_render();');s=b.replace_once(s,'return mm_install_options_speed() &&','return mm_install_options_render() && mm_install_options_speed() &&');f.write_text(s,encoding='utf-8')
 f=OUT/'build.cmd';f.write_text(b.replace_once(f.read_text(),'options_speed.cpp /link','options_speed.cpp options_render.cpp /link'))
 ws=OUT/'wrapper';shutil.copytree(SOURCE/'wrapper',ws,ignore=shutil.ignore_patterns('bin','obj','Debug','Release','.vs'))
 h=(b.SRC/'display_render.h').read_text();(ws/'src/display_render.h').write_text(h);(ws/'src/display_render_load.h').write_text(h[:h.index('static UINT mm_display_render_message')]+'\n#endif\n')
 f=ws/'src/config.c';s=f.read_text();s=b.replace_once(s,'#include "display_resolution_load.h"','#include "display_resolution_load.h"\n#include "display_render_load.h"');s=b.replace_once(s,'    mm_display_load_resolution();','    mm_display_load_resolution();\n    mm_display_load_render();');f.write_text(s)
 f=ws/'src/wndproc.c';s=f.read_text();s=b.replace_once(s,'#include "display_resolution.h"','#include "display_resolution.h"\n#include "display_render.h"\nextern LONG mm_render_successful_presents;');s=b.replace_once(s,'    if(uMsg==mm_display_window_message()', '    if(uMsg==mm_display_render_message() && mm_mixed_enabled())return mm_display_apply_render(wParam,lParam);\n    if(uMsg==mm_display_window_message()');s=b.replace_once(s,'        if (wParam == WM_APP + 80) return', '        if (wParam == WM_APP + 82) return InterlockedExchangeAdd(&mm_render_successful_presents,0);\n        if (wParam == WM_APP + 83) return g_config.maxfps;\n        if (wParam == WM_APP + 80) return');f.write_text(s)
 f=ws/'src/render_d3d9.c';s=f.read_text();s='LONG mm_render_successful_presents;\n'+s if False else s
 # Count only successful real Present calls, not loop iterations.
 s=b.replace_once(s,'DWORD WINAPI d3d9_render_main(void)','LONG mm_render_successful_presents;\n\nDWORD WINAPI d3d9_render_main(void)')
 s=b.replace_once(s,'        else\n        {\n            /* Force redraw for GDI games (ClueFinders) */','        else\n        {\n            InterlockedIncrement(&mm_render_successful_presents);\n            /* Force redraw for GDI games (ClueFinders) */');f.write_text(s)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
 assert all(resources(OUT/n)[i]==current[i] for n in ['candidate.exe','release.exe'] for i in [101,103])
 subprocess.run([str(b.MSBUILD),'cnc-ddraw.vcxproj','/p:Configuration=Release','/p:Platform=Win32','/m','/v:minimal'],cwd=ws,check=True)
def label_bytes(raw):
 raw,n=re.subn(rb'(?m)^(STR_19\s*=\s*)[^\r\n]*',lambda m:m[1]+'渲染帧率'.encode('gbk'),raw);assert n==1 and b'STR_98' not in raw
 return raw+b'\r\nSTR_98 = 60 FPS\r\nSTR_99 = 120 FPS\r\n'
def screen_bytes(raw):
 for n,k in [(5,98),(6,99)]:
  raw,count=re.subn(rb'(\[RADIOBUTTON_'+str(n).encode()+rb'\][\s\S]*?\bText=)\d+',lambda m:m[1]+str(k).encode(),raw);assert count==1
 raw,n=re.subn(rb'\[RADIOBUTTON_7\][\s\S]*?(?=\[RADIOBUTTON_8\])',b'',raw);assert n==1
 # Native builds radio IDs by ordinal; retaining a hidden third control avoids shifting later event IDs.
 hidden=b'\r\n[RADIOBUTTON_7]\r\nFont=SMALL\r\nRect2=0,0,0,0\r\nRect1=0,0,0,0\r\nText=98; unused legacy third slot\r\n\r\n'
 raw=raw.replace(b'[RADIOBUTTON_8]',hidden+b'[RADIOBUTTON_8]')
 return raw
def install():
 import install_options_resolution as i
 a=json.loads((OUT/'runtime-acceptance.json').read_text());assert a['result']=='passed' and a['candidate_sha256']==b.sha(OUT/'candidate.exe') and a['wrapper_sha256']==b.sha(OUT/'wrapper/bin/Release/ddraw.dll')
 base.write(OUT/'verification.json',dict(result='passed',module_sha256=b.sha(OUT/'qol_bindings.dll'),wrapper_sha256=b.sha(OUT/'wrapper/bin/Release/ddraw.dll'),runtime_acceptance=a))
 i.OUT=OUT;i.BACK=BACK;i.label_bytes=label_bytes;i.MANIFEST_FIELD='options_render';i.EXTRA_RUNTIME_CHANGES=[(SCREEN,screen_bytes)];i.install()
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('action',choices=['build','install']);globals()[a.parse_args().action]()
