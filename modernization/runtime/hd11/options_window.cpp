#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstring>
namespace {
int selected_window_mode(){
 char value[32]={0};
 GetPrivateProfileStringA("display","window_mode","windowed",value,sizeof value,".\\remastered-settings.ini");
 return !strcmp(value,"borderless");
}
struct Target {UINT message;HWND window;unsigned matches;};
BOOL CALLBACK find_window(HWND window,LPARAM context){
 auto target=(Target*)context;DWORD owner=0;GetWindowThreadProcessId(window,&owner);
 if(owner!=GetCurrentProcessId())return TRUE;
 DWORD_PTR reply=0;
 if(SendMessageTimeoutA(window,target->message,0,0,SMTO_ABORTIFHUNG,250,&reply) && reply==0x4D4D4450){target->window=window;++target->matches;}
 return TRUE;
}
void __cdecl select_window_mode(int borderless){
 WritePrivateProfileStringA("display","window_mode",borderless?"borderless":"windowed",".\\remastered-settings.ini");
 Target target={RegisterWindowMessageA("MagicMayhem.Remastered.Display.v1"),NULL,0};
 EnumWindows(find_window,(LPARAM)&target);
 if(target.matches==1)PostMessageA(target.window,RegisterWindowMessageA("MagicMayhem.Remastered.Window.v1"),borderless,0);
}
DWORD setup_continuation=0x4a9512,apply_continuation=0x4a9949;
__declspec(naked) void window_setup(){__asm{
 pushfd
 pushad
 call selected_window_mode
 mov [esp+20],eax
 popad
 popfd
 jmp dword ptr [setup_continuation]
}}
__declspec(naked) void window_apply(){__asm{
 pushfd
 pushad
 push ecx
 call select_window_mode
 add esp,4
 popad
 popfd
 jmp dword ptr [apply_continuation]
}}
bool patch(BYTE* site,const BYTE* expected,void* entry){
 if(memcmp(site,expected,6))return false;
 DWORD old,ignored;if(!VirtualProtect(site,6,PAGE_EXECUTE_READWRITE,&old))return false;
 BYTE code[6]={0xe9,0,0,0,0,0x90};*(DWORD*)(code+1)=(DWORD)entry-(DWORD)site-5;
 memcpy(site,code,6);FlushInstructionCache(GetCurrentProcess(),site,6);VirtualProtect(site,6,old,&ignored);return true;
}
}
extern "C" bool mm_install_options_window(){
 const BYTE setup[]={0x8b,0x15,0xf1,0xe6,0x6d,0},apply[]={0x89,0x0d,0xf1,0xe6,0x6d,0};
 if(memcmp((void*)0x4a950c,setup,6)||memcmp((void*)0x4a9943,apply,6))return false;
 return patch((BYTE*)0x4a950c,setup,window_setup)&&patch((BYTE*)0x4a9943,apply,window_apply);
}
