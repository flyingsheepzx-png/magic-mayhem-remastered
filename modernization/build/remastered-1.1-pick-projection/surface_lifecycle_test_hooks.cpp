#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstring>
#include "surface_registry.h"
namespace {
using Destroy=void(__thiscall*)(void*);
using Create=int(__thiscall*)(void*,DWORD*,const char*,int);
Destroy destroy_native;Create create_native;
DWORD release_base_return=0x2058b40b,release_surface_return=0x2058b41c;
// A control may reset its base interface (+4) before recreating the surface,
// while the queried interface (+8) is still registered and needs releasing.
// Native Destroy only tests +8, then blindly dereferences +4. Skip just the
// missing interface; retain native queried-surface/palette cleanup and registry.
__declspec(naked) void release_base_if_present(){__asm{
    mov eax,[esi+4]
    pushfd
    test eax,eax
    jz absent_base
    popfd
    inc edi
    push eax
    jmp dword ptr [release_base_return]
absent_base:
    popfd
    jmp dword ptr [release_surface_return]
}}
bool registered(void* object){
    auto table=(void**)0x206f6950;unsigned count=*(unsigned*)0x206f8154;
    if(count>128)return false;
    for(unsigned i=0;i<count;++i)if(table[i]==object)return true;
    return false;
}
void __fastcall destroy_surface(void* object,void*){
    auto table=(void**)0x206f6950;auto count=(unsigned*)0x206f8154;
    if(*count<=128 && registered(object)){
        // The object index is not authoritative after recreation. Remove all
        // aliases first, then present exactly one live entry to native Release.
        *count=mm_surface::compact(table,*count,object,[](void* p,unsigned i){*(unsigned*)((char*)p+0x1c)=i;});
        if(*(void**)((char*)object+8)){
            table[*count]=object;*(unsigned*)((char*)object+0x1c)=(*count)++;
        }
    }
    destroy_native(object);
}
int __fastcall create_surface(void* object,void*,DWORD* desc,const char* file,int line){
    // Native Create appends without unregistering a previous incarnation.
    if(registered(object))destroy_surface(object,nullptr);
    return create_native(object,desc,file,line);
}
void* trampoline(unsigned site){
    auto code=(unsigned char*)VirtualAlloc(nullptr,10,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
    if(!code)return nullptr;
    memcpy(code,(void*)site,5);code[5]=0xe9;*(DWORD*)(code+6)=site+5-(DWORD)(code+10);
    FlushInstructionCache(GetCurrentProcess(),code,10);return code;
}
bool hook(unsigned site,void* target){
    DWORD old=0,unused=0;if(!VirtualProtect((void*)site,5,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char code[5]={0xe9};*(DWORD*)(code+1)=(DWORD)target-site-5;
    memcpy((void*)site,code,5);FlushInstructionCache(GetCurrentProcess(),(void*)site,5);
    VirtualProtect((void*)site,5,old,&unused);return true;
}
}
extern "C" bool mm_install_surface_lifecycle(){
    const unsigned char create[]={0xa1,0x54,0x81,0x6f,0x20};
    const unsigned char destroy[]={0x53,0x56,0x8b,0xf1,0x57};
    const unsigned char release_base[]={0x8b,0x46,0x04,0x47,0x50};
    if(memcmp((void*)0x2058ad90,create,5)||memcmp((void*)0x2058b3e0,destroy,5)||
       memcmp((void*)0x2058b406,release_base,5))return false;
    create_native=(Create)trampoline(0x2058ad90);destroy_native=(Destroy)trampoline(0x2058b3e0);
    return create_native && destroy_native && hook(0x2058b406,release_base_if_present) &&
        hook(0x2058b3e0,destroy_surface) && hook(0x2058ad90,create_surface);
}
