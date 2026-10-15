// Disposable 30-logic-tick movement timing probe for the known community EXE.
#include <windows.h>
#include <stdio.h>
#include <string.h>

static HANDLE logfile=INVALID_HANDLE_VALUE;
static DWORD resume_address=0x5104d7;
struct Phase { void* unit; int remainder; };
static Phase phases[4096];
static bool original_walltime_trial;
static int __cdecl effective_speed(void* unit) {
    int original=*(int*)((char*)unit+0xb63);
    if (*(int*)0x6de6fd!=30 || *(int*)0x6e1f0c>1 ||
        original<=0 || original>1000000) return original;
    unsigned id=*(unsigned short*)unit;
    if (id>=4096) return original;
    Phase& phase=phases[id];
    if (phase.unit!=unit) {phase.unit=unit;phase.remainder=0;}
    int numerator=original*(original_walltime_trial?31:2)+phase.remainder;
    int denominator=original_walltime_trial?50:3;
    phase.remainder=numerator%denominator;
    // Preserve native speed/acceleration fields. Scale only the amount
    // added to the animation/motion accumulator on this logic tick.
    return numerator/denominator;
}
__declspec(naked) static void speed_hook() {
    __asm {
        pushfd
        pushad
        push ebp
        call effective_speed
        add esp,4
        mov [esp+28],eax
        popad
        popfd
        jmp dword ptr [resume_address]
    }
}
static bool patch(unsigned address,void* target,const unsigned char* expected,unsigned length) {
    if (memcmp((void*)address,expected,length)) return false;
    DWORD previous;
    if (!VirtualProtect((void*)address,length,PAGE_EXECUTE_READWRITE,&previous)) return false;
    unsigned char bytes[8]={0xe9,0,0,0,0,0x90,0x90,0x90};
    *(DWORD*)(bytes+1)=(DWORD)target-address-5;
    memcpy((void*)address,bytes,length);
    FlushInstructionCache(GetCurrentProcess(),(void*)address,length);
    DWORD unused;VirtualProtect((void*)address,length,previous,&unused);
    return true;
}
static BOOL logic_time_initialize(HINSTANCE h) {
        DisableThreadLibraryCalls(h);
        char setting[4]={0};
        GetEnvironmentVariableA("MM_PROBE_ORIGINAL_WALLTIME",setting,sizeof(setting));
        original_walltime_trial=setting[0]=='1' && !setting[1];
        const unsigned char expected[]={0x8b,0x85,0x63,0x0b,0x00,0x00};
        if (memcmp((void*)0x5104d1,expected,sizeof(expected))) return FALSE;
        logfile=CreateFileA("modernization\\logs\\logic-time-trial.csv",FILE_APPEND_DATA,
            FILE_SHARE_READ|FILE_SHARE_WRITE,0,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
        if (!patch(0x5104d1,(void*)speed_hook,expected,sizeof(expected))) return FALSE;
    return TRUE;
}
#ifdef MM_ALL_IN_ONE
extern "C" BOOL __cdecl mm_logic_time_initialize(HINSTANCE h){return logic_time_initialize(h);}
#else
BOOL WINAPI DllMain(HINSTANCE h,DWORD reason,LPVOID){
    return reason==DLL_PROCESS_ATTACH?logic_time_initialize(h):TRUE;
}
#endif
