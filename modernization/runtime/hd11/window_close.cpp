// Known-engine Alt+F4 compatibility shim: queue WM_CLOSE, then return from
// the key callback before native WM_DESTROY releases scene/input resources.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstring>
namespace {
__declspec(naked) void alt_f4_close(){__asm{
    // Enter from disk shim with pushfd/pushad already on the stack.
    // Original WndProc hwnd at +0x4c, plus saved 0x24 => +0x70.
    mov eax,[esp+70h]
    push 0
    push 0
    push 10h
    push eax
    call dword ptr ds:[5c5270h]
    popad
    popfd
    // Skip the stale scene callback after requesting close.
    push 4ea124h
    ret
}}
bool jump(unsigned address,void* target,unsigned length){
 DWORD old=0,unused=0;
 if(!VirtualProtect((void*)address,length,PAGE_EXECUTE_READWRITE,&old))return false;
 unsigned char bytes[8]={0xe9,0,0,0,0,0x90,0x90,0x90};
 *(DWORD*)(bytes+1)=(DWORD)target-address-5;
 memcpy((void*)address,bytes,length);
 FlushInstructionCache(GetCurrentProcess(),(void*)address,length);
 VirtualProtect((void*)address,length,old,&unused);return true;
}
}
extern "C" bool mm_install_window_close(){
 // Gate both shortcuts before modifying either. Other keys remain native.
 const unsigned char alt[]={0x6a,0,0xe8,0x98,0x34,0xfd,0xff};
 const unsigned char title[]={0x81,0x7c,0x24,0x14,0xa1,0,0,0};
 if(memcmp((void*)0x5c4271,alt,sizeof(alt)) ||
    memcmp((void*)0x5c4294,title,sizeof(title)))return false;
 // The title-button shortcut used PostQuitMessage too. Resume the normal
 // TranslateMessage/DispatchMessage path so DefWindowProc handles SC_CLOSE.
 return jump(0x5c4271,alt_f4_close,7) && jump(0x5c4294,(void*)0x5c42b1,8);
}
