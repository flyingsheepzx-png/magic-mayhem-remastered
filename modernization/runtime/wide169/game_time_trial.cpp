// Disposable single-player 30-Hz loop, original-wall-time game-clock trial.
// Update iteration still runs every tick; only the global time count is paced.
#include <windows.h>
#include <string.h>

static int phase;
static DWORD resume=0x46b49b;
static int __cdecl next_game_tick() {
    int now=*(int*)0x6c4830;
    if (*(int*)0x6de6fd!=30 || *(int*)0x6e1f0c>1) return now+1;
    phase+=20;
    if (phase>=33){phase-=33;return now+1;}
    return now;
}
__declspec(naked) static void tick_hook(){__asm{
    pushfd
    pushad
    call next_game_tick
    mov [esp+28],eax
    popad
    popfd
    mov ecx,dword ptr [6e1f14h]
    cmp eax,ecx
    push edx
    mov edx,6c4830h
    mov [edx],eax
    pop edx
    jmp dword ptr [resume]
}}
static BOOL game_time_initialize(HINSTANCE module){
    DisableThreadLibraryCalls(module);
    const unsigned char expected[]={0xa1,0x30,0x48,0x6c,0x00,0x8b,0x0d,0x14,0x1f,0x6e,0x00};
    if(memcmp((void*)0x46b488,expected,sizeof(expected)))return FALSE;
    DWORD old;if(!VirtualProtect((void*)0x46b488,sizeof(expected),PAGE_EXECUTE_READWRITE,&old))return FALSE;
    unsigned char bytes[11]={0xe9};*(DWORD*)(bytes+1)=(DWORD)tick_hook-0x46b488-5;
    memset(bytes+5,0x90,6);memcpy((void*)0x46b488,bytes,11);
    FlushInstructionCache(GetCurrentProcess(),(void*)0x46b488,11);
    DWORD unused;VirtualProtect((void*)0x46b488,11,old,&unused);
    return TRUE;
}
#ifdef MM_ALL_IN_ONE
extern "C" BOOL __cdecl mm_game_time_initialize(HINSTANCE module){return game_time_initialize(module);}
#else
BOOL WINAPI DllMain(HINSTANCE module,DWORD reason,LPVOID){
    return reason==DLL_PROCESS_ATTACH?game_time_initialize(module):TRUE;
}
#endif
