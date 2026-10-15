// Single-player NOTIONAL allowance only. Keep native timing and multiplayer.
#include <windows.h>
#include <cstdint>
#include <cstring>

extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_budget_a_hook(){__asm{
    mov eax,dword ptr ds:[5e15f4h]
    pushfd
    cmp dword ptr ds:[6e1f0ch],0
    jne native_a
    cmp dword ptr ds:[6e1f64h],0
    jne native_a
    mov eax,300
native_a:
    popfd
    push 46b5c3h
    ret
}}
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_budget_b_hook(){__asm{
    mov eax,dword ptr ds:[5e15f4h]
    pushfd
    cmp dword ptr ds:[6e1f0ch],0
    jne native_b
    cmp dword ptr ds:[6e1f64h],0
    jne native_b
    mov eax,300
native_b:
    popfd
    push 46b5d8h
    ret
}}

extern "C" bool mm_install_ai_budget(){
    constexpr unsigned char expected[]={0xa1,0xf4,0x15,0x5e,0};
    const unsigned sites[]={0x46b5be,0x46b5d3};
    void* hooks[]={reinterpret_cast<void*>(mm_ai_budget_a_hook),reinterpret_cast<void*>(mm_ai_budget_b_hook)};
    // Validate both sites before either write. Launcher already hash-gates engine.
    for(unsigned site:sites)if(std::memcmp(reinterpret_cast<void*>(site),expected,5))return false;
    for(unsigned i=0;i<2;i++){
        auto* site=reinterpret_cast<unsigned char*>(sites[i]);
        DWORD old=0,unused=0;
        if(!VirtualProtect(site,5,PAGE_EXECUTE_READWRITE,&old))return false;
        unsigned char jump[]={0xe9,0,0,0,0};
        *reinterpret_cast<int*>(jump+1)=static_cast<int>(reinterpret_cast<uintptr_t>(hooks[i])-sites[i]-5);
        std::memcpy(site,jump,5);
        FlushInstructionCache(GetCurrentProcess(),site,5);
        if(!VirtualProtect(site,5,old,&unused))return false;
    }
    return true;
}
