// Disposable high-resolution scheduler clock for the verified community build.
// Does not implement game-time compensation or 60 distinct rendered frames.
#include <windows.h>
#include <stdint.h>
#include <string.h>

static LARGE_INTEGER origin,frequency;
static DWORD base_ms;
static DWORD WINAPI precise_tick_count() {
    LARGE_INTEGER now;QueryPerformanceCounter(&now);
    return base_ms+(DWORD)((now.QuadPart-origin.QuadPart)*1000/frequency.QuadPart);
}
static BOOL clock_initialize(HINSTANCE instance) {
        DisableThreadLibraryCalls(instance);
        const unsigned char timer_bytes[]={0x8b,0x35,0x64,0x51,0x5c,0x00};
        if (memcmp((void*)0x4e3e5b,timer_bytes,sizeof(timer_bytes))) return FALSE;
        auto real=(DWORD (WINAPI*)())GetProcAddress(GetModuleHandleW(L"kernel32.dll"),"GetTickCount");
        if (!real || *(void**)0x5c5164!=(void*)real ||
            !QueryPerformanceFrequency(&frequency) || frequency.QuadPart<=0) return FALSE;
        base_ms=real();QueryPerformanceCounter(&origin);
        DWORD previous;
        if (!VirtualProtect((void*)0x5c5164,sizeof(void*),PAGE_READWRITE,&previous)) return FALSE;
        *(void**)0x5c5164=(void*)precise_tick_count;
        DWORD unused;VirtualProtect((void*)0x5c5164,sizeof(void*),previous,&unused);
    return TRUE;
}
#ifdef MM_ALL_IN_ONE
extern "C" BOOL __cdecl mm_clock_initialize(HINSTANCE instance){return clock_initialize(instance);}
#else
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID){
    return reason==DLL_PROCESS_ATTACH?clock_initialize(instance):TRUE;
}
#endif
