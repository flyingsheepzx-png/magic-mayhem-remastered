// Increase bounded single-player perception throughput; native arithmetic intact.
#include <windows.h>
#include <cstdint>
#include <cstring>
extern "C" __declspec(dllexport) __declspec(naked) void mm_danger_units_hook(){__asm{
    cmp dword ptr ds:[6e1f0ch],0
    jne native_units
    cmp eax,16
    jmp restore_unit_store
native_units:
    cmp eax,4
restore_unit_store:
    mov dword ptr [esi+1209dh],edi
    push 41dc06h
    ret
}}
extern "C" __declspec(dllexport) __declspec(naked) void mm_danger_cells_hook(){__asm{
    cmp dword ptr ds:[6e1f0ch],0
    jne native_cells
    cmp esi,128
    jmp cell_branch
native_cells:
    cmp esi,32
cell_branch:
    je cell_yield
    push 41d405h
    ret
cell_yield:
    push 41dc10h
    ret
}}
// After completing the last owner at the rotation cap, restart scanning next
// invocation instead of finalizing that exhausted owner's empty scratch again.
extern "C" __declspec(dllexport) __declspec(naked) void mm_danger_rotation_hook(){__asm{
    cmp ecx,eax
    jne rotation_continue
    pushfd
    cmp dword ptr ds:[6e1f0ch],0
    jne rotation_native_exit
    mov byte ptr [edi+12098h],1
rotation_native_exit:
    popfd
    push 41dc10h
    ret
rotation_continue:
    push 41d48eh
    ret
}}
extern "C" bool mm_install_ai_danger_refresh(){
    const unsigned sites[]={0x41dbfd,0x41d3fc,0x41d486};
    const unsigned sizes[]={9,9,8};
    const unsigned char expected[][9]={{0x83,0xf8,4,0x89,0xbe,0x9d,0x20,1,0},
        {0x83,0xfe,0x20,0x0f,0x84,0x0b,8,0,0},
        {0x3b,0xc8,0x0f,0x84,0x82,7,0,0,0}};
    void* hooks[]={reinterpret_cast<void*>(mm_danger_units_hook),reinterpret_cast<void*>(mm_danger_cells_hook),reinterpret_cast<void*>(mm_danger_rotation_hook)};
    for(unsigned i=0;i<3;i++)if(std::memcmp(reinterpret_cast<void*>(sites[i]),expected[i],sizes[i]))return false;
    for(unsigned i=0;i<3;i++){
        DWORD old=0,unused=0;auto* site=reinterpret_cast<unsigned char*>(sites[i]);
        if(!VirtualProtect(site,sizes[i],PAGE_EXECUTE_READWRITE,&old))return false;
        unsigned char jump[]={0xe9,0,0,0,0,0x90,0x90,0x90,0x90};
        *reinterpret_cast<int*>(jump+1)=static_cast<int>(reinterpret_cast<uintptr_t>(hooks[i])-sites[i]-5);
        std::memcpy(site,jump,sizes[i]);FlushInstructionCache(GetCurrentProcess(),site,sizes[i]);
        if(!VirtualProtect(site,sizes[i],old,&unused))return false;
    }
    return true;
}
