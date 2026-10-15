#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstring>
extern "C" __declspec(dllexport) volatile LONG mm_options_logic_updates=0;
namespace {
DWORD prior_tick;
__declspec(naked) void counted_tick(){__asm{
 pushfd
 lock inc dword ptr [mm_options_logic_updates]
 popfd
 jmp dword ptr [prior_tick]
}}
bool diagnostic_counter(){
 char enabled[4]={0};GetEnvironmentVariableA("MM_PROBE_OPTIONS_LOGIC",enabled,sizeof enabled);
 if(strcmp(enabled,"1"))return true;
 auto site=(BYTE*)0x46b488;
 if(site[0]!=0xe9 || memcmp(site+5,"\x90\x90\x90\x90\x90\x90",6))return false;
 prior_tick=(DWORD)site+5+*(DWORD*)(site+1);
 MEMORY_BASIC_INFORMATION region;
 if(!VirtualQuery((void*)prior_tick,&region,sizeof region))return false;
 if(prior_tick-(DWORD)region.AllocationBase!=0x7c80)return false;
 const BYTE expected[]={0x9c,0x60,0xe8,0xb9,0xff,0xff,0xff,0x89,0x44,0x24,0x1c,0x61};
 if(memcmp((void*)prior_tick,expected,sizeof expected))return false;
 DWORD old,ignored;if(!VirtualProtect(site,5,PAGE_EXECUTE_READWRITE,&old))return false;
 *(DWORD*)(site+1)=(DWORD)counted_tick-(DWORD)site-5;
 FlushInstructionCache(GetCurrentProcess(),site,5);VirtualProtect(site,5,old,&ignored);return true;
}
}
extern "C" bool mm_install_options_speed(){
 // Whole native instructions: setup thresholds and apply constants only.
 struct Change {DWORD address;BYTE before[5];BYTE after[5];unsigned length;};
 const Change changes[]={
  {0x4a9571,{0x83,0xf8,0x14},{0x83,0xf8,0x28},3},
  {0x4a9584,{0x83,0xf8,0x11},{0x83,0xf8,0x1e},3},
  {0x4a9a04,{0xb9,0x0e,0,0,0},{0xb9,0x14,0,0,0},5},
  {0x4a9a0b,{0xb9,0x11,0,0,0},{0xb9,0x1e,0,0,0},5},
  {0x4a9a12,{0xb9,0x14,0,0,0},{0xb9,0x28,0,0,0},5}
 };
 for(auto& c:changes)if(memcmp((void*)c.address,c.before,c.length))return false;
 for(auto& c:changes){
  DWORD old,ignored;if(!VirtualProtect((void*)c.address,c.length,PAGE_EXECUTE_READWRITE,&old))return false;
  memcpy((void*)c.address,c.after,c.length);FlushInstructionCache(GetCurrentProcess(),(void*)c.address,c.length);
  VirtualProtect((void*)c.address,c.length,old,&ignored);
 }
 return diagnostic_counter();
}
