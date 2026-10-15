"""Execute compiled detours with OS/settings boundaries stubbed only."""
import sys,re,struct,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'modernization/tools'))
import prepare_options_resolution as b
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
out=b.OUT;pe=pefile.PE(str(out/'qol_bindings.dll'));image=pe.get_memory_mapped_image();base=pe.OPTIONAL_HEADER.ImageBase
mapping=(out/'qol_bindings.map').read_text()
def symbol(name):
 rows=[line for line in mapping.splitlines() if '?'+name+'@' in line]
 assert len(rows)==1,(name,rows)
 return int(re.search(r'\s([0-9a-fA-F]{8})\s+f',rows[0])[1],16)
setup=symbol('resolution_setup');apply=symbol('resolution_apply');load=symbol('selected_high');select=symbol('select_resolution')
registers=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EFLAGS]
count=0
for high in [0,1]:
 for flag in range(64):
  for entry,end in [(setup,0x4a94be),(apply,0x4a991f)]:
   u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(base,(len(image)+4095)&~4095);u.mem_write(base,image);u.mem_map(0x400000,0x300000);u.mem_map(0x1000000,0x10000)
   for i,r in enumerate(registers[:-2]):u.reg_write(r,0x102000+i*256)
   u.reg_write(UC_X86_REG_EAX,high);u.reg_write(UC_X86_REG_ESP,0x1008000)
   flags=2|sum(1<<bit for i,bit in enumerate([0,2,4,6,7,11]) if flag&(1<<i));u.reg_write(UC_X86_REG_EFLAGS,flags)
   u.mem_write(0x6de6d5,struct.pack('<I',1));before=[u.reg_read(r) for r in registers];calls=[]
   def boundary(uc,a,size,data):
    if a not in [load,select]:return
    sp=uc.reg_read(UC_X86_REG_ESP);ret=struct.unpack('<I',uc.mem_read(sp,4))[0]
    if a==select:calls.append(struct.unpack('<I',uc.mem_read(sp+4,4))[0])
    uc.reg_write(UC_X86_REG_EAX,high);uc.reg_write(UC_X86_REG_ECX,0xbad);uc.reg_write(UC_X86_REG_EDX,0xbad)
    uc.reg_write(UC_X86_REG_ESP,sp+4);uc.reg_write(UC_X86_REG_EIP,ret)
   u.hook_add(UC_HOOK_CODE,boundary);u.emu_start(entry,end,count=80)
   expected=before[:]
   if entry==setup:expected[1]=high
   assert [u.reg_read(r) for r in registers]==expected
   assert u.mem_read(0x6de6d5,4)==struct.pack('<I',1)
   assert calls==([high] if entry==apply else [])
   count+=1
source=r'''
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cassert>
#include <cstdio>
struct Config {RECT window_rect;BOOL fullscreen;BOOL windowed;BOOL border;} g_config;
static int resets;
static HRESULT dd_SetDisplayMode(DWORD w,DWORD h,DWORD b,DWORD f){assert(!w&&!h&&!b&&!f);++resets;return S_OK;}
#include "display_resolution.h"
int main(){
 const char* path=".\\remastered-settings.ini";
 DeleteFileA(path);
 assert(mm_display_width()==0);
 for(int w: {1920,2560}){
  WritePrivateProfileStringA("display","resolution",w==1920?"1920x1080":"2560x1440",path);
  assert(mm_display_width()==w);g_config.fullscreen=TRUE;mm_display_load_resolution();
  assert(g_config.window_rect.right==w && g_config.window_rect.bottom==w*9/16 && !g_config.fullscreen);
  assert(mm_display_apply_resolution(w,w*9/16));
 }
 assert(resets==2);assert(!mm_display_apply_resolution(800,600));assert(!mm_display_apply_resolution(1920,1440));
 WritePrivateProfileStringA("display","resolution","corrupt",path);assert(!mm_display_width());
 DeleteFileA(path);puts("Native persistence/load/live reset validation passed");
}
'''.replace('#include <cstdio>','#include <cstdio>\n#include <initializer_list>')
(out/'display_test.cpp').write_text(source)
(out/'test.cmd').write_text(f'@echo off\ncall "{b.b.VC}" x86 >nul\ncl /nologo /O2 /EHsc /std:c++17 /I"{b.b.SRC}" display_test.cpp /link /OUT:display_test.exe\nif errorlevel 1 exit /b 1\ndisplay_test.exe\n')
subprocess.run(['cmd','/c','test.cmd'],cwd=out,check=True)
engine=b.base.DEST/'runtime/Chaos-Wide169-engine.exe';ep=pefile.PE(str(engine))
assert ep.get_data(0xa990c,19)==bytes.fromhex('8b0dd5e66d003bc17409a3d5e66d00c6466701')
assert ep.get_data(0xa94b8,6)==bytes.fromhex('8b1dd5e66d00')
b.base.write(out/'verification.json',dict(result='passed',module_sha256=b.b.sha(out/'qol_bindings.dll'),wrapper_sha256=b.b.sha(out/'wrapper/bin/Release/ddraw.dll'),compiled_hook_cases=count,native_settings_test=True,runtime_acceptance='pending user testing; no gameplay launched'))
print(count,'compiled hook cases passed; internal geometry unmodified')
