#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstring>
namespace {
int selected_render(){return GetPrivateProfileIntA("display","render_fps",60,".\\remastered-settings.ini")==120?1:0;}
struct Target {UINT message;HWND window;unsigned matches;};
BOOL CALLBACK find_window(HWND window,LPARAM context){
 auto target=(Target*)context;DWORD owner=0;GetWindowThreadProcessId(window,&owner);
 if(owner!=GetCurrentProcessId())return TRUE;
 DWORD_PTR reply=0;
 if(SendMessageTimeoutA(window,target->message,0,0,SMTO_ABORTIFHUNG,250,&reply) && reply==0x4D4D4450){target->window=window;++target->matches;}
 return TRUE;
}
void __cdecl select_render(void* page){
 auto group=*(unsigned char**)((unsigned char*)page+0x63)+0x20;
 int count=*(int*)(group+8),index=*(int*)(group+4);
 if(index<0 || index>=count)return;
 auto control=((unsigned char**)*(void**)group)[index];
 int event=*(int*)(control+0x2d);if(event!=4 && event!=5)return;
 int fps=event==5?120:60;
 WritePrivateProfileStringA("display","render_fps",fps==120?"120":"60",".\\remastered-settings.ini");
 Target target={RegisterWindowMessageA("MagicMayhem.Remastered.Display.v1"),NULL,0};
 EnumWindows(find_window,(LPARAM)&target);
 if(target.matches==1)PostMessageA(target.window,RegisterWindowMessageA("MagicMayhem.Remastered.Render.v1"),fps,0);
}
DWORD setup_continuation=0x4a953c,apply_continuation=0x4a99dd;
__declspec(naked) void render_setup(){__asm{
 pushfd
 pushad
 call selected_render
 mov [esp+28],eax
 popad
 popfd
 jmp dword ptr [setup_continuation]
}}
__declspec(naked) void render_apply(){__asm{
 pushfd
 pushad
 push esi
 call select_render
 add esp,4
 popad
 popfd
 jmp dword ptr [apply_continuation]
}}
}
extern "C" bool mm_install_options_render(){
 const BYTE setup[]={0xa1,0xf5,0xe6,0x6d,0};
 // Branch bytes verified in full in the builder against the immutable engine.
 const BYTE begin[]={0x8b,0x46,0x63,0x8b,0x48,0x28};
 if(memcmp((void*)0x4a9537,setup,5)||memcmp((void*)0x4a9949,begin,6))return false;
 DWORD old,ignored;
 if(!VirtualProtect((void*)0x4a9537,5,PAGE_EXECUTE_READWRITE,&old))return false;
 BYTE patch[5]={0xe9};*(DWORD*)(patch+1)=(DWORD)render_setup-0x4a9537-5;
 memcpy((void*)0x4a9537,patch,5);FlushInstructionCache(GetCurrentProcess(),(void*)0x4a9537,5);VirtualProtect((void*)0x4a9537,5,old,&ignored);
 // Redirect at the beginning of a complete native block; continuation reloads EAX.
 if(!VirtualProtect((void*)0x4a9949,6,PAGE_EXECUTE_READWRITE,&old))return false;
 BYTE code[6]={0xe9,0,0,0,0,0x90};*(DWORD*)(code+1)=(DWORD)render_apply-0x4a9949-5;
 memcpy((void*)0x4a9949,code,6);FlushInstructionCache(GetCurrentProcess(),(void*)0x4a9949,6);VirtualProtect((void*)0x4a9949,6,old,&ignored);return true;
}
