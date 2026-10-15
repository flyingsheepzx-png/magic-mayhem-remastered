"""Wrapper-only completed-redraw presentation; retain concurrent AI launcher."""
import argparse,json,shutil,subprocess,hashlib
from pathlib import Path
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from build_11_fmv_h264 import replace
OUT=b.ROOT/'modernization/build/remastered-1.1-transition-present-v6'
BACK=b.ROOT/'modernization/backups/remastered-1.1-transition-present-v6'
OLD='4ff43a636ab7ef95e465921a1920c2e45c93357c5b42c3dd4e71ab0cb5d4749b'
def build():
 source=b.ROOT/'modernization/build/remastered-1.1-battle-hud/wrapper'
 assert b.sha(source/'bin/Release/ddraw.dll')=='37f27f5c295229f9e5ba510ceffc390214fb278bbbc0fafde24791ae79e876e5'
 rows=[]
 for e,m,k in base.targets():
  d=json.loads(m.read_text(encoding='utf-8'))
  assert b.sha(e)==d['launcher_sha256'] and b.sha(e.parent/'runtime/ddraw.dll')==OLD
  assert b.sha(e.parent/'runtime/Chaos-Wide169-engine.exe')==d['engine_sha256']=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
  rows.append(dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)))
 OUT.mkdir(exist_ok=False);base.write(OUT/'before.json',rows)
 ws=OUT/'wrapper';shutil.copytree(source,ws,ignore=shutil.ignore_patterns('.git','bin','obj','Debug','Release','.vs'))
 shutil.copy2(b.SRC/'presentation_epoch.h',ws/'src/presentation_epoch.h')
 p=ws/'src/mm_mixed.h';s=p.read_text()
 s=b.replace_once(s,'extern LONG mm_mixed_d3d9_uploads;','extern LONG mm_mixed_d3d9_uploads;\nBOOL mm_mixed_redraw_begin(IDirectDrawSurfaceImpl* primary);\nvoid mm_mixed_redraw_end(IDirectDrawSurfaceImpl* primary,int mode);')
 s=b.replace_once(s,'static unsigned char* mm_mixed_pixels;','''#include "presentation_epoch.h"
static MmPresentationEpoch mm_epoch;
static int mm_redraw_mode;
static unsigned char* mm_last_pixels;
static SIZE_T mm_last_capacity;
static IDirectDrawSurfaceImpl mm_last_surface;
static int mm_battle_art_ready(IDirectDrawSurfaceImpl* p);
static unsigned mm_control_signature(void){
    unsigned h=2166136261u;int i,count=*(int*)MM_HD_CONTROL_COUNT;
    if(count<0 || count>400)return 0;
    h=(h^(unsigned)count)*16777619u;
    for(i=0;i<count;++i){
        const unsigned char* p=((const unsigned char**)MM_HD_CONTROL_TABLE)[i];
        unsigned v;int rect[4],j;
        if(!mm_hd_readable(p,0x21))return 0;
        v=*(unsigned*)p;memcpy(rect,p+0x11,sizeof rect);
        h=(h^(unsigned)(SIZE_T)p)*16777619u;h=(h^v)*16777619u;
        for(j=0;j<4;++j)h=(h^(unsigned)rect[j])*16777619u;
    }
    return h;
}
BOOL mm_mixed_redraw_begin(IDirectDrawSurfaceImpl* p) {
    return mm_mixed_enabled() && p && (p->caps&DDSCAPS_PRIMARYSURFACE) &&
        p->width==2560 && p->height==1440 && p->bpp==16;
}
void mm_mixed_redraw_end(IDirectDrawSurfaceImpl* p,int mode) {
    (void)p;
    if(mode==MM_HD_BATTLE && mm_epoch.ready && mm_epoch.mode==MM_HD_UI &&
       !mm_battle_art_ready(p))return;
    if(mm_epoch_redraw(&mm_epoch,mode,mm_control_signature(),GetTickCount()))mm_redraw_mode=mode;
}
static IDirectDrawSurfaceImpl* mm_remember(IDirectDrawSurfaceImpl* p) {
    SIZE_T n=(SIZE_T)p->pitch*p->height;
    if(mm_last_capacity<n){
        unsigned char* q=(unsigned char*)HeapAlloc(GetProcessHeap(),0,n);
        if(!q)return p;
        if(mm_last_pixels)HeapFree(GetProcessHeap(),0,mm_last_pixels);
        mm_last_pixels=q;mm_last_capacity=n;
    }
    memcpy(mm_last_pixels,p->surface,n);mm_last_surface=*p;
    mm_last_surface.surface=mm_last_pixels;return p;
}
static unsigned char* mm_mixed_pixels;''')
 s=b.replace_once(s,'IDirectDrawSurfaceImpl* mm_mixed_present(IDirectDrawSurfaceImpl* primary)\n{','''static IDirectDrawSurfaceImpl* mm_mixed_compose(IDirectDrawSurfaceImpl* primary)
{''')
 s=b.replace_once(s,'!mm_mixed_is_battle(primary))','mm_redraw_mode!=MM_HD_BATTLE)')
 s=b.replace_once(s,'#include "mm_battle_hud.h"','''#include "mm_battle_hud.h"
static int mm_battle_art_ready(IDirectDrawSurfaceImpl* p){
    const unsigned char* control=(const unsigned char*)0x6c4e40;
    int r[4],x,y,dim;unsigned n;
    mm_hud_load();if(!mm_hud_count)return 1;
    if(!mm_hd_readable(control,0x21))return 0;
    memcpy(r,control+0x11,16);
    if(r[0]<0 || r[1]<0 || r[2]>1280 || r[3]>720)return 0;
    for(n=0;n<mm_hud_count;++n){
        MmHudTile* t=mm_hud_tiles+n;if(t->kind!=3)continue;
        for(dim=0;dim<3;++dim)
            for(y=r[1]-8;y<=r[3]-(int)t->h+8;++y)
                for(x=r[0]-8;x<=r[2]-(int)t->w+8;++x)
                    if(mm_hud_match(t,(const unsigned char*)p->surface,p->pitch,x,y,dim))return 1;
    }
    return 0;
}''')
 s=b.replace_once(s,'POINT mm_mixed_input_point(IDirectDrawSurfaceImpl* primary, int x, int y)\n{','''IDirectDrawSurfaceImpl* mm_mixed_present(IDirectDrawSurfaceImpl* primary)
{
    if(!mm_mixed_redraw_begin(primary))return primary;
    if(mm_epoch.ready && (mm_epoch.mode!=mm_hd_current().mode ||
       mm_epoch.signature!=mm_control_signature()) && mm_last_pixels)
        return &mm_last_surface;
    if(!mm_epoch.ready)mm_redraw_mode=mm_hd_current().mode;
    return mm_remember(mm_mixed_compose(primary));
}

POINT mm_mixed_input_point(IDirectDrawSurfaceImpl* primary, int x, int y)
{''')
 p.write_text(s)
 p=ws/'src/ddsurface.c';whole=p.read_text();cut=whole.index('HRESULT dds_BltFast(');s=whole[:cut];suffix=whole[cut:];s=b.replace_once(s,'#include "palette.h"','#include "palette.h"\n#include "mm_mixed.h"')
 s=b.replace_once(s,'    void* dst_buf = dds_GetBuffer(This);','''    /* Serialize primary blit and its mode stamp with the renderer. Controls
       are sampled on the game thread before pixels, never on the upload thread. */
    BOOL mm_primary=mm_mixed_redraw_begin(This);
    int mm_mode=mm_primary?mm_hd_current().mode:0;
    if(mm_primary)EnterCriticalSection(&g_ddraw.cs);
    void* dst_buf = dds_GetBuffer(This);''')
 needle='    if ((This->caps & DDSCAPS_PRIMARYSURFACE) && g_ddraw.ref && g_ddraw.render.run)'
 pos=s.index(needle)
 s=s[:pos]+'''    if(mm_primary){
        if(src_surface && dst_buf && src_buf && dst_x==0 && dst_y==0 &&
           dst_w==This->width && dst_h==This->height)
            mm_mixed_redraw_end(This,mm_mode);
        LeaveCriticalSection(&g_ddraw.cs);
    }

'''+s[pos:]
 end=suffix.index('HRESULT dds_',20);fast=suffix[:end];rest=suffix[end:]
 fast=b.replace_once(fast,'    void* dst_buf = dds_GetBuffer(This);','''    BOOL mm_primary=mm_mixed_redraw_begin(This);
    int mm_mode=mm_primary?mm_hd_current().mode:0;
    if(mm_primary)EnterCriticalSection(&g_ddraw.cs);
    void* dst_buf = dds_GetBuffer(This);''')
 fast=b.replace_once(fast,needle,'''    if(mm_primary){
        if(src_surface && dst_buf && src_buf && dst_x==0 && dst_y==0 &&
           dst_w==This->width && dst_h==This->height)
            mm_mixed_redraw_end(This,mm_mode);
        LeaveCriticalSection(&g_ddraw.cs);
    }

'''+needle)
 p.write_text(s+fast+rest)
 subprocess.run([str(b.MSBUILD),'cnc-ddraw.vcxproj','/p:Configuration=Release','/p:Platform=Win32','/m','/v:minimal'],cwd=ws,check=True)
 subprocess.run([__import__('sys').executable,str(b.ROOT/'modernization/tests/presentation_epoch_test.py')],check=True)
 base.write(OUT/'verification.json',dict(result='passed',wrapper_sha256=b.sha(ws/'bin/Release/ddraw.dll'),tests='compiled transition schedules; source gating and full-primary commit checks',runtime_acceptance='pending user testing; no gameplay launched',scope='wrapper-only; all launcher modules including AI budget untouched'))
def install():
 base.idle();v=json.loads((OUT/'verification.json').read_text());assert v['result']=='passed'
 dll=OUT/'wrapper/bin/Release/ddraw.dll';assert b.sha(dll)==v['wrapper_sha256']
 BACK.mkdir(exist_ok=False);changes=[]
 for i,r in enumerate(json.loads((OUT/'before.json').read_text())):
  e,m=Path(r['entry']),Path(r['manifest']);assert b.sha(e)==r['entry_sha256'] and b.sha(m)==r['manifest_sha256']
  d=json.loads(m.read_text(encoding='utf-8'));key='ddraw.dll' if r['kind']=='candidate' else 'runtime/ddraw.dll'
  p=e.parent/'runtime/ddraw.dll';assert b.sha(p)==OLD
  d['files'][key]=v['wrapper_sha256'];d['transition_presentation']=v
  for j,(dest,data) in enumerate([(p,dll.read_bytes()),(m,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())]):
   bak=BACK/f'{i}-{j}.bak';bak.write_bytes(dest.read_bytes());changes.append(dict(path=str(dest),backup=str(bak),before_sha256=b.sha(dest),after_sha256=hashlib.sha256(data).hexdigest(),data=data))
 base.write(BACK/'rollback.json',[{k:v for k,v in r.items() if k!='data'} for r in changes])
 try:
  for r in changes:replace(Path(r['path']),r['data']);assert b.sha(Path(r['path']))==r['after_sha256']
 except BaseException:
  for r in changes:replace(Path(r['path']),Path(r['backup']).read_bytes())
  raise
 for r in json.loads((OUT/'before.json').read_text()):assert b.sha(Path(r['entry']))==r['entry_sha256']
 print('Installed wrapper-only transition fix; all launchers preserved')
def rollback():
 base.idle();rows=json.loads((BACK/'rollback.json').read_text())
 for r in rows:assert b.sha(Path(r['path']))==r['after_sha256'] and b.sha(Path(r['backup']))==r['before_sha256']
 for r in rows:replace(Path(r['path']),Path(r['backup']).read_bytes())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','install','rollback']);globals()[p.parse_args().action]()
