"""Execute the actual compositor with synthetic pixels and controlled page state."""
import sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'modernization/tools'))
import build_11_transition_present as b
ws=b.OUT/'wrapper';test=b.OUT/'presentation_test.cpp'
# Stub only engine eligibility / live control and HD overlay boundaries. Actual
# compositor, copied pixels, frame hold and ready mode execute unmodified.
s=(ws/'src/mm_mixed.h').read_text()
start=s.index('static int mm_battle_art_ready(IDirectDrawSurfaceImpl* p){');end=s.index('static IDirectDrawSurfaceImpl* mm_mixed_compose',start)
s=s[:start]+'static int mm_battle_art_ready(IDirectDrawSurfaceImpl* p){return art_ready;}\n'+s[end:]
s=s.replace('#include "layout_context.h"','').replace('#include "ddsurface.h"','').replace('#include "dd.h"','').replace('#include "mm_engine_identity.h"','').replace('#include "mm_battle_hud.h"','')
start=s.index('BOOL mm_mixed_enabled(void)\n{');end=s.index('\n/* The engine keeps pixels',start)
s=s[:start]+'BOOL mm_mixed_enabled(void){return TRUE;}\n'+s[end:]
start=s.index('static unsigned mm_control_signature(void)');end=s.index('BOOL mm_mixed_redraw_begin(',start)
s=s[:start]+'static unsigned mm_control_signature(void){return signature;}\n'+s[end:]
s=s.replace('mm_control_signature(),GetTickCount()','mm_control_signature(),frame')
(b.OUT/'test_mixed.h').write_text(s)
test.write_text(r'''
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cassert>
#include <cstdio>
#include <vector>
#include <cstring>
#define DDSCAPS_PRIMARYSURFACE 0x200
#define MM_HD_BATTLE 1
#define MM_HD_UI 2
struct IDirectDrawSurfaceImpl {void* surface;int width,height,bpp,pitch;DWORD caps;};
struct MmHdLayoutContext {int mode;};
static int live=2;
static int art_ready=1;
static unsigned frame=0,signature=2;
static MmHdLayoutContext mm_hd_current(){return {live};}
static POINT mm_hd_input(MmHdLayoutContext c,int x,int y){return {x/(c.mode==1?2:1),y/(c.mode==1?2:1)};}
static void mm_hud_present(IDirectDrawSurfaceImpl*,unsigned char*){}
#define MM_MIXED_IMPLEMENTATION
#include "test_mixed.h"
int main(){
 std::vector<unsigned short> pixels(2560*1440);
 IDirectDrawSurfaceImpl p={pixels.data(),2560,1440,16,5120,DDSCAPS_PRIMARYSURFACE};
 unsigned cases=0;
 for(int repeat=0;repeat<64;++repeat){
  // Full UI background is drawn at native size; no crop/2x.
  live=2;signature=2;std::fill(pixels.begin(),pixels.end(),0x1234);
  mm_mixed_redraw_end(&p,2);++frame;
  mm_mixed_redraw_end(&p,2);
  assert(mm_mixed_present(&p)->surface==p.surface);
  live=1;signature=1;
  // Controls replaced early: the old UI must not become an enlarged quadrant.
  for(int partial=0;partial<8;++partial){
   pixels[partial]=0xabcd;
   auto held=mm_mixed_present(&p);
   assert(held->surface!=p.surface);
   assert(((unsigned short*)held->surface)[partial]==0x1234);
   ++cases;
  }
  // Complete battle copy commits its policy and scales source coordinates.
  std::fill(pixels.begin(),pixels.end(),0x5678);
  pixels[0]=0x1111;pixels[719*2560+1279]=0x2222;
  art_ready=0;
  for(int early=0;early<4;++early){
   ++frame;mm_mixed_redraw_end(&p,1);
   assert(((unsigned short*)mm_mixed_present(&p)->surface)[0]==0x1234);
   ++cases;
  }
  art_ready=1;
  mm_mixed_redraw_end(&p,1);++frame;mm_mixed_redraw_end(&p,1);
  auto shown=mm_mixed_present(&p);
  auto out=(unsigned short*)shown->surface;
  assert(out[0]==0x1111 && out[2561]==0x1111);
  assert(out[1440*2560-1]==0x2222);
  assert(pixels[1]==0x5678); // Native primary never modified by scale/cache.
  // Same-mode removal of a confirmation overlay must also wait for redraw.
  signature=3;pixels[0]=0xeeee;mm_mixed_redraw_end(&p,1);
  assert(((unsigned short*)mm_mixed_present(&p)->surface)[0]==0x1111);
  pixels[0]=0x1111;++frame;mm_mixed_redraw_end(&p,1);mm_mixed_present(&p);++cases;
  auto click=mm_mixed_input_point(&p,2558,1438);
  assert(click.x==1279 && click.y==719);
  live=2;signature=2;
  // Exit replaces controls before the panel is complete. Hold prior battle.
  for(int partial=0;partial<8;++partial){
   pixels[partial]=0xeeee;
   auto held=(unsigned short*)mm_mixed_present(&p)->surface;
   assert(held[0]==0x1111 && held[1440*2560-1]==0x2222);
   ++cases;
  }
  std::fill(pixels.begin(),pixels.end(),0x3333);
  mm_mixed_redraw_end(&p,2);++frame;mm_mixed_redraw_end(&p,2);
  assert(mm_mixed_present(&p)->surface==p.surface);
  click=mm_mixed_input_point(&p,2558,1438);
  assert(click.x==2558 && click.y==1438);
  cases+=2;
 }
 printf("%u actual compositor transition cases passed; pixel/input/source checks\n",cases);
}
''')
(b.OUT/'test.cmd').write_text(f'''@echo off
call "{b.b.VC}" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 /I"{ws/'src'}" presentation_test.cpp /link /OUT:presentation_test.exe
if errorlevel 1 exit /b 1
presentation_test.exe
''')
subprocess.run(['cmd','/c','test.cmd'],cwd=b.OUT,check=True)
print('Real compositor preserves both complete page types across early controls and partial writes')
