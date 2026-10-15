#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstring>
namespace { DWORD portrait_resume=0x4d3c96; }
// Native selection remains active while battle sprite banks are being released.
// Reject only the incomplete bank, before acquiring any drawing surface/context.
// Retrying the ordinary portrait repaint uses the original four-frame artwork.
extern "C" __declspec(dllexport) __declspec(naked) void mm_portrait_sprite_ready(){__asm{
    pushfd
    cmp dword ptr ds:[0x6593e0],0
    je not_ready
    cmp dword ptr ds:[0x6593e8],0
    je not_ready
    cmp dword ptr ds:[0x6593ec],0
    je not_ready
    popfd
    push ecx
    mov eax,ds:[0x6a4646]
    jmp dword ptr [portrait_resume]
not_ready:
    popfd
    ret
}}
extern "C" bool mm_install_portrait_sprite_ready(){
    const unsigned char expected[]={0x51,0xa1,0x46,0x46,0x6a,0};
    auto site=(unsigned char*)0x4d3c90;
    if(memcmp(site,expected,sizeof expected))return false;
    DWORD old=0,unused=0;
    if(!VirtualProtect(site,sizeof expected,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char patch[6]={0xe9,0,0,0,0,0x90};
    *(DWORD*)(patch+1)=(DWORD)mm_portrait_sprite_ready-(DWORD)site-5;
    memcpy(site,patch,sizeof patch);
    FlushInstructionCache(GetCurrentProcess(),site,sizeof patch);
    VirtualProtect(site,sizeof patch,old,&unused);return true;
}
