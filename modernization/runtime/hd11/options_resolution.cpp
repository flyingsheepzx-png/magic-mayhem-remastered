#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstring>
namespace {
int selected_high(){
    char value[32]={0};
    GetPrivateProfileStringA("display","resolution","2560x1440",value,sizeof value,".\\remastered-settings.ini");
    return strcmp(value,"1920x1080")!=0;
}
struct DisplayTarget {UINT message;HWND window;unsigned matches;};
BOOL CALLBACK find_display_window(HWND window,LPARAM context){
    auto target=(DisplayTarget*)context;DWORD owner=0;
    GetWindowThreadProcessId(window,&owner);
    if(owner!=GetCurrentProcessId())return TRUE;
    DWORD_PTR reply=0;
    if(SendMessageTimeoutA(window,target->message,0,0,SMTO_ABORTIFHUNG,250,&reply)
       && reply==0x4D4D4450){target->window=window;++target->matches;}
    return TRUE;
}
void __cdecl select_resolution(int high){
    WritePrivateProfileStringA("display","resolution",high?"2560x1440":"1920x1080",".\\remastered-settings.ini");
    UINT message=RegisterWindowMessageA("MagicMayhem.Remastered.Display.v1");
    DisplayTarget target={message,NULL,0};
    EnumWindows(find_display_window,(LPARAM)&target);
    if(target.matches==1)PostMessageA(target.window,message,high?2560:1920,high?1440:1080);
}
DWORD continuation=0x4a991f;
DWORD setup_continuation=0x4a94be;
__declspec(naked) void resolution_setup(){__asm{
    pushfd
    pushad
    call selected_high
    mov [esp+16],eax
    popad
    popfd
    jmp dword ptr [setup_continuation]
}}
__declspec(naked) void resolution_apply(){__asm{
    pushfd
    pushad
    push eax
    call select_resolution
    add esp,4
    popad
    popfd
    jmp dword ptr [continuation]
}}
}
extern "C" bool mm_install_options_resolution(){
    const BYTE expected[]={0x8b,0x0d,0xd5,0xe6,0x6d,0,0x3b,0xc1,0x74,0x09,0xa3,0xd5,0xe6,0x6d,0,0xc6,0x46,0x67,0x01};
    auto site=(BYTE*)0x4a990c;
    // Exact whole-instruction branch is19 bytes, continuing at4a991f.
    const BYTE setup[]={0x8b,0x1d,0xd5,0xe6,0x6d,0};
    if(memcmp(site,expected,19) || memcmp((void*)0x4a94b8,setup,6))return false;
    DWORD old=0,ignored=0;if(!VirtualProtect(site,19,PAGE_EXECUTE_READWRITE,&old))return false;
    BYTE patch[19];memset(patch,0x90,sizeof patch);patch[0]=0xe9;
    *(DWORD*)(patch+1)=(DWORD)resolution_apply-(DWORD)site-5;
    memcpy(site,patch,sizeof patch);FlushInstructionCache(GetCurrentProcess(),site,sizeof patch);
    VirtualProtect(site,sizeof patch,old,&ignored);
    site=(BYTE*)0x4a94b8;
    if(!VirtualProtect(site,6,PAGE_EXECUTE_READWRITE,&old))return false;
    BYTE code[6]={0xe9,0,0,0,0,0x90};*(DWORD*)(code+1)=(DWORD)resolution_setup-(DWORD)site-5;
    memcpy(site,code,6);FlushInstructionCache(GetCurrentProcess(),site,6);
    VirtualProtect(site,6,old,&ignored);return true;
}
