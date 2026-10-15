// Native Portmanteau drag bounds must match the enlarged mitems frame canvas.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdint>
#include <cstring>
#include "layout_context.h"
namespace {
using Draw=void(__thiscall*)(void*);
Draw original;
void __fastcall draw(void* owner,void*){
    int saved[4];auto* sizes=(int*)0x5c774c;
    memcpy(saved,sizes,sizeof(saved));
    // Native index +0x24c selects 800/640 geometry; +8 selects height.
    // Scope the shared constants to this call, including its native restore pass.
    if(mm_hd_current().mode==MM_HD_UI){
        int factor=mm_hd_current().font_scale;
        for(int i=0;i<4;i++)sizes[i]=saved[i]*factor;
    }
    original(owner);
    memcpy(sizes,saved,sizeof(saved));
}
}
extern "C" bool mm_install_port_drag(){
    const BYTE expected[]={0x81,0xec,0x00,0x02,0x00,0x00};
    const int sizes[]={83,66,83,66};
    if(memcmp((void*)0x576830,expected,6) || memcmp((void*)0x5c774c,sizes,16))return false;
    auto* code=(BYTE*)VirtualAlloc(nullptr,11,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
    if(!code)return false;
    memcpy(code,expected,6);code[6]=0xe9;
    *(int32_t*)(code+7)=(int32_t)(0x576836-(uintptr_t)(code+11));original=(Draw)code;
    DWORD table_old;
    if(!VirtualProtect((void*)0x5c774c,16,PAGE_READWRITE,&table_old))return false;
    // Keep the shared table writable for scoped save/scale/restore calls.
    DWORD old,unused; if(!VirtualProtect((void*)0x576830,6,PAGE_EXECUTE_READWRITE,&old))return false;
    BYTE replacement[]={0xe9,0,0,0,0,0x90};
    *(int32_t*)(replacement+1)=(int32_t)((uintptr_t)draw-0x576835);
    memcpy((void*)0x576830,replacement,6);FlushInstructionCache(GetCurrentProcess(),(void*)0x576830,6);
    return VirtualProtect((void*)0x576830,6,old,&unused)!=0;
}
