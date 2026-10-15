"""Owned diagnostic wrapper: actual primary operations and presented frame pairs."""
import argparse,shutil,subprocess,time,ctypes
from pathlib import Path
import compare_remastered_ui_11 as c
import build_remastered_11 as b
import build_11_surface_lifecycle as base
OUT=b.ROOT/'modernization/build/transition-frame-diagnostic-v6'
def build():
 OUT.mkdir(exist_ok=False)
 source=b.ROOT/'modernization/build/remastered-1.1-transition-present-v6/wrapper'
 ws=OUT/'wrapper';shutil.copytree(source,ws,ignore=shutil.ignore_patterns('bin','obj','Debug','Release','.vs'))
 p=ws/'src/mm_mixed.h';s=p.read_text()
 s=s.replace('extern LONG mm_mixed_d3d9_uploads;','extern LONG mm_mixed_d3d9_uploads;\nvoid mm_trace_blt(int x,int y,int w,int h,int mode);')
 s=s.replace('static MmPresentationEpoch mm_epoch;','''#include <stdio.h>
static FILE* mm_trace;
static FILE* mm_trace_pixels;
static unsigned mm_trace_count;
static int mm_trace_armed(void){
    if(GetFileAttributesA("transition.capture")==INVALID_FILE_ATTRIBUTES)return 0;
    if(!mm_trace){fopen_s(&mm_trace,"transition-events.csv","wb");fopen_s(&mm_trace_pixels,"transition-frames.bin","wb");}
    return mm_trace!=NULL && mm_trace_count<600;
}
void mm_trace_blt(int x,int y,int w,int h,int mode){
    if(mm_trace_armed()){
        fprintf(mm_trace,"B,%lu,%u,%d,%d,%d,%d,%d\\n",GetTickCount(),mm_trace_count,x,y,w,h,mode);fflush(mm_trace);
    }
}
static void mm_trace_frame(IDirectDrawSurfaceImpl* native,IDirectDrawSurfaceImpl* shown,int epoch,int ready){
    unsigned short row[640];int which,y,x;
    if(!mm_trace_armed() || !mm_trace_pixels || native->width!=2560 || native->bpp!=16)return;
    fprintf(mm_trace,"P,%lu,%u,%d,%d,%d,%d\\n",GetTickCount(),mm_trace_count,mm_hd_current().mode,epoch,ready,*(int*)0x642c68);fflush(mm_trace);
    for(which=0;which<2;++which){
        IDirectDrawSurfaceImpl* p=which?shown:native;
        for(y=0;y<1440;y+=4){
            unsigned short* pixels=(unsigned short*)((unsigned char*)p->surface+y*p->pitch);
            for(x=0;x<640;++x)row[x]=pixels[x*4];
            fwrite(row,2,640,mm_trace_pixels);
        }
    }
    fflush(mm_trace_pixels);++mm_trace_count;
}
static MmPresentationEpoch mm_epoch;''')
 s=s.replace('IDirectDrawSurfaceImpl* mm_mixed_present(IDirectDrawSurfaceImpl* primary)\n{','static IDirectDrawSurfaceImpl* mm_mixed_original_present(IDirectDrawSurfaceImpl* primary)\n{')
 key='POINT mm_mixed_input_point(IDirectDrawSurfaceImpl* primary, int x, int y)\n{'
 s=s.replace(key,'''IDirectDrawSurfaceImpl* mm_mixed_present(IDirectDrawSurfaceImpl* primary){
    IDirectDrawSurfaceImpl* result=mm_mixed_original_present(primary);
    if(primary && primary->surface)mm_trace_frame(primary,result,mm_epoch.mode,mm_epoch.ready);
    return result;
}
'''+key);p.write_text(s)
 p=ws/'src/ddsurface.c';s=p.read_text();s=s.replace('    if(mm_primary){\n        if(src_surface','    if(mm_primary){\n        mm_trace_blt(dst_x,dst_y,dst_w,dst_h,mm_mode);\n        if(src_surface')
 start=s.index('HRESULT dds_BltFast(');end=s.index('HRESULT dds_',start+20)
 part=s[start:end];needle='    if ((This->caps & DDSCAPS_PRIMARYSURFACE) && g_ddraw.ref && g_ddraw.render.run)'
 part=part.replace(needle,'    if(mm_mixed_redraw_begin(This))mm_trace_blt(dst_x,dst_y,dst_w,dst_h,mm_hd_current().mode);\n'+needle)
 s=s[:start]+part+s[end:];p.write_text(s)
 subprocess.run([str(b.MSBUILD),'cnc-ddraw.vcxproj','/p:Configuration=Release','/p:Platform=Win32','/m','/v:minimal'],cwd=ws,check=True)
def run(name,wrapper=None,new_game=False):
 ctypes.windll.user32.SetProcessDPIAware()
 p=base.DEST;identity=dict(version='1.1',package=str(p),launcher_name=base.ENTRY,launcher_sha256=c.sha(p/base.ENTRY),engine_sha256=c.ENGINES['1.1'])
 out=b.ROOT/'modernization/logs/remastered-ui'/name;out.mkdir(exist_ok=False)
 rt=c.stage(identity,out/'package',p/'runtime/Save/14.sav')
 from install_11_minimap_v2 import resources
 candidate=b.TARGET/'MagicMayhem-Remastered-1.1.exe'
 assert resources(candidate)==resources(p/base.ENTRY)
 shutil.copy2(candidate,rt.parent/base.ENTRY);identity['launcher_sha256']=c.sha(candidate)
 shutil.copy2(wrapper or OUT/'wrapper/bin/Release/ddraw.dll',rt/'ddraw.dll')
 s=c.session_class()(identity,rt,out/'1.1',100)
 from probe_11_close_wait import chains
 started=time.monotonic();last=[0];observer=[None];av=out/'exception';av.mkdir()
 def startup_state():
  if observer[0] is None:
   helper=b.ROOT/'modernization/build/hang-dump-x86/capture_first_av_x86.exe'
   observer[0]=subprocess.Popen([str(helper),str(s.pid),str((rt/'Chaos-Wide169-engine.exe').resolve()),str(av.resolve()),'25'],stdout=(av/'helper.txt').open('w'))
  if time.monotonic()-started>8 and not last[0]:
   last[0]=1
   c.write_json(out/'startup-waits.json',chains(s.pid))
   c.write_json(out/'startup-controls.json',s.controls())
   from ctypes import wintypes as W
   rows=[]
   s.u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,ctypes.c_int];s.u.GetClassNameW.argtypes=[W.HWND,W.LPWSTR,ctypes.c_int]
   def visit(h,unused):
    pid=W.DWORD();s.u.GetWindowThreadProcessId(h,ctypes.byref(pid))
    if pid.value in [s.pid,s.proc.pid]:
     title=ctypes.create_unicode_buffer(512);cls=ctypes.create_unicode_buffer(128);s.u.GetWindowTextW(h,title,512);s.u.GetClassNameW(h,cls,128)
     rows.append(dict(hwnd=h,title=title.value,cls=cls.value,visible=bool(s.u.IsWindowVisible(h))))
    return True
   s.u.EnumWindows(s.cb(visit),0);c.write_json(out/'startup-windows.json',rows)
 s.startup_ui_action=startup_state
 with s:
  (rt/'transition.capture').touch()
  if new_game:
   s.click_base(640,396);c.wait_control(s,lambda r:r['rect']==[1880,60,2024,204])
   s.shot('new-map',False);c.write_json(out/'new-map-controls.json',s.controls())
   s.click_base(384,642);time.sleep(3);s.shot('new-click',False);c.write_json(out/'new-click-controls.json',s.controls())
  else:s.load_fixture('14')
  c.wait_control(s,lambda r:r['vtable']=='0x5c6f54')
  time.sleep(.5);s.shot('battle14',False)
  s.key(0x1b);time.sleep(.3);c.write_json(out/'escape-controls.json',s.controls());s.shot('escape',False)
  # Native Escape menu: Quit to campaign/main menu.
  s.click_base(640,420);time.sleep(.3);c.write_json(out/'quit-controls.json',s.controls());s.shot('quit',False)
  s.click_base(503,454);time.sleep(2);s.shot('returned',False)
  # Confirmation choices are recorded before any further action.
  time.sleep(.5)
  c.write_json(out/'final-controls.json',s.controls())
 for f in ['transition-events.csv','transition-frames.bin']:shutil.copy2(rt/f,out/f)
 print(out,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);p.add_argument('--name',default='transition-live-before');p.add_argument('--wrapper',type=Path);p.add_argument('--new-game',action='store_true');a=p.parse_args();build() if a.action=='build' else run(a.name,a.wrapper,a.new_game)
