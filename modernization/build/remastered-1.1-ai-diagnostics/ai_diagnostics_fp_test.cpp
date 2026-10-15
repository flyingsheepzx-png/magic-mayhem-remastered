// Run real x86 FXSAVE/FXRSTOR around the SAME callback macro as the shipped hooks.
// This is an offline DLL fixture, not a game process or a runtime acceptance run.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <string.h>
static void (__cdecl* roundtrip)();
__declspec(align(16)) static unsigned char before_fp[512],after_fp[512],caller_fp[512];
static unsigned before_regs[8],after_regs[8],before_flags,after_flags;
static unsigned short control=0xb7f;
static unsigned csr=0x3f80;
__declspec(naked) static void capture() {
    __asm {
        pushfd
        pushad
        fxsave caller_fp
        fninit
        fld1
        fld1
        fld1
        fld1
        fld1
        fld1
        fld1
        fld1
        fldcw control
        ldmxcsr csr
        pcmpeqd xmm0,xmm0
        pcmpeqd xmm1,xmm1
        pcmpeqd xmm2,xmm2
        pcmpeqd xmm3,xmm3
        pcmpeqd xmm4,xmm4
        pcmpeqd xmm5,xmm5
        pcmpeqd xmm6,xmm6
        pcmpeqd xmm7,xmm7
        mov eax,0x12345678
        mov ecx,0x87654321
        mov edx,0x24681357
        mov ebx,0x13572468
        mov esi,0x55443322
        mov edi,0x11223344
        mov ebp,0x66778899
        std
        pushfd
        pop before_flags
        mov before_regs,eax
        mov before_regs+4,ecx
        mov before_regs+8,edx
        mov before_regs+12,ebx
        mov before_regs+16,esp
        mov before_regs+20,ebp
        mov before_regs+24,esi
        mov before_regs+28,edi
        fxsave before_fp
        call dword ptr [roundtrip]
        fxsave after_fp
        mov after_regs,eax
        mov after_regs+4,ecx
        mov after_regs+8,edx
        mov after_regs+12,ebx
        mov after_regs+16,esp
        mov after_regs+20,ebp
        mov after_regs+24,esi
        mov after_regs+28,edi
        pushfd
        pop after_flags
        cld
        fxrstor caller_fp
        popad
        popfd
        ret
    }
}
int main() {
    SetEnvironmentVariableA("MM_AI_TRACE",nullptr);
    HMODULE dll=LoadLibraryW(L"ai_fixture.dll");
    if(!dll){printf("fixture load failed %lu\n",GetLastError());return 1;}
    roundtrip=(void(__cdecl*)())GetProcAddress(dll,"mm_ai_test_roundtrip");
    auto begin=(void(__cdecl*)())GetProcAddress(dll,"mm_ai_test_begin");
    if(!roundtrip || !begin)return 2;
    for(int enabled=0;enabled<2;enabled++) {
        if(enabled)begin();
        SetLastError(0x12345678);capture();
        if(memcmp(before_fp,after_fp,sizeof(before_fp)) ||
           memcmp(before_regs,after_regs,sizeof(before_regs)) ||
           before_flags!=after_flags || GetLastError()!=0x12345678) {
            printf("state mismatch enabled=%d\n",enabled);
            for(int i=0;i<512;i++)if(before_fp[i]!=after_fp[i])printf("FP[%d]=%02x/%02x\n",i,before_fp[i],after_fp[i]);
            return 3;
        }
    }
    puts("Real x86 callback preserves all GPRs, flags/DF, full x87 state including IP/DP, XMM/MXCSR and LastError (off/on)");
    fflush(stdout);
    // Fixture fake handle must not be closed during native process-detach.
    ExitProcess(0);
}
