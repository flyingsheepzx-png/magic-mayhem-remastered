// Optional observation only; native decisions, RNG, timing configuration and
// learned files are untouched. Engine identity is checked by launcher AND DLL.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <bcrypt.h>
#include <stdint.h>
#include <string.h>

static const char engine_sha[]="42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da";
struct Registers { uint32_t edi,esi,ebp,esp,ebx,edx,ecx,eax,flags; };
struct Event {
    uint32_t kind,seq,tick,side,phase,scheduler,group,action,id,vtable,subject;
    uint32_t old_action,old_id,budget,result,score,other_score,source,count;
    uint32_t elapsed_us,data[80];
};
static_assert(sizeof(Event)==400,"decoder layout");
static HANDLE output=INVALID_HANDLE_VALUE;
static Event events[128];
static unsigned used,sequence,written;
static LARGE_INTEGER frequency,started[2];
static bool active=false;
static const unsigned kMaxBytes=32*1024*1024;

// Diagnostic reads use the native, already-live objects. Bounds/SEH also make
// stale or malformed data produce incomplete telemetry instead of game failure.
static uint32_t word(uint32_t address) {
    if(address<0x10000 || address>0x7ffffffb)return 0;
    __try { return *(const uint32_t*)address; }
    __except(EXCEPTION_EXECUTE_HANDLER) { return 0; }
}
static unsigned byte(uint32_t address) {
    if(address<0x10000 || address>0x7fffffff)return 0;
    __try { return *(const unsigned char*)address; }
    __except(EXCEPTION_EXECUTE_HANDLER) { return 0; }
}
static void flush() {
    if(!active || !used)return;
    DWORD bytes=used*sizeof(Event),actual=0;
    if(written+bytes>kMaxBytes || !WriteFile(output,events,bytes,&actual,nullptr) || actual!=bytes) {
        active=false;CloseHandle(output);output=INVALID_HANDLE_VALUE;used=0;return;
    }
    written+=bytes;used=0;
}
static void action_info(Event& e,unsigned a) {
    e.action=a;e.id=word(a+4);e.vtable=word(a);e.subject=word(a+0x27);
    e.group=word(a+8);e.score=word(a+0x1b);
}
static void scheduler_info(Event& e,unsigned scheduler) {
    e.scheduler=scheduler;e.side=word(scheduler);e.tick=word(scheduler+0x14);
    e.phase=word(scheduler+0x11dab);
}
static void vector_copy(Event& e,unsigned vector) {
    unsigned start=word(vector+4),end=word(vector+8);
    if(start<0x10000 || end<start || (end-start)%4 || end-start>80*4)return;
    e.count=(end-start)/4;
    for(unsigned i=0;i<e.count;i++)e.data[i]=word(start+4*i);
}
extern "C" __declspec(dllexport) void __cdecl mm_ai_observe(unsigned kind,const Registers* r) {
    if(!active || word(0x6e1f0c)!=0)return; // multiplayer stays native/unobserved
    DWORD error=GetLastError();
    Event e={};e.kind=kind;e.seq=++sequence;e.tick=word(0x6c4830);
    unsigned sp=r->esp+4; // PUSHFD precedes PUSHAD
    switch(kind) {
    case 1: // scheduler entry, thiscall(budget)
        scheduler_info(e,r->ecx);e.budget=word(sp+4);
        if(e.side<2)QueryPerformanceCounter(&started[e.side]);
        break;
    case 2: { // scheduler exit, all native paths converge here
        scheduler_info(e,r->esi);
        LARGE_INTEGER now;QueryPerformanceCounter(&now);
        if(e.side<2 && started[e.side].QuadPart && frequency.QuadPart)
            e.elapsed_us=(unsigned)((now.QuadPart-started[e.side].QuadPart)*1000000/frequency.QuadPart);
        break;
    }
    case 3: // model input: thiscall(id, feature vector, nout, output)
        e.id=word(sp+4);e.source=word(sp);vector_copy(e,word(sp+8));
        break;
    case 4: { // model exit: prologue consumed 0xdc bytes, native args retained
        e.id=word(sp+0xe0);e.source=word(sp+0xdc);
        unsigned count=word(sp+0xe8),dest=word(sp+0xec);
        if(count<=80 && dest>=0x10000) {
            e.count=count;for(unsigned i=0;i<count;i++)e.data[i]=word(dest+4*i);
        }
        break;
    }
    case 5: // evaluator returned, including pending/incomplete result
    case 6:
        scheduler_info(e,r->esi);action_info(e,word(word(r->ebp-8)));
        e.group=r->edi;e.result=r->eax&255;e.score=word(r->ebp+8);
        e.budget=word(word(r->ebp+0xc)+8);e.source=kind==5?0x428674:0x4288d4;
        break;
    case 7: // eligible candidate, BEFORE native reservoir/random selection
    case 8: // another evaluation requested; reason deliberately not guessed
        scheduler_info(e,r->esi);action_info(e,word(word(r->ebp-8)));
        e.group=r->edi;e.score=word(r->ebp+8);e.other_score=word(r->esi+0x11ddd);
        e.old_action=word(r->ebp+0x14);e.old_id=word(e.old_action+4);
        e.budget=word(word(r->ebp+0xc)+8);
        break;
    case 9: // verified budget-yield path
        scheduler_info(e,r->esi);action_info(e,word(r->ebx));e.group=r->edi;
        e.budget=word(word(r->ebp+0xc)+8);e.result=byte(r->ebp-1);
        break;
    case 10: // selected action committed to group
        scheduler_info(e,r->ecx);action_info(e,word(word(r->ecx+0x11fe5)));
        e.group=word(sp+4);e.old_action=word(e.group+5);e.old_id=word(e.old_action+4);
        e.score=word(r->ecx+0x11ddd);
        break;
    case 11: // native execution result, 0 makes native set action +0x14
        scheduler_info(e,r->esi);action_info(e,r->edi);e.result=r->eax&255;
        e.budget=word(r->ebp-0x14);
        break;
    case 12: // native retirement check; BL says removal selected, not why
        scheduler_info(e,r->ebp);action_info(e,r->esi);e.result=r->ebx&255;
        e.other_score=word(r->esi+0x10);e.budget=0;
        break;
    default: SetLastError(error);return;
    }
    events[used++]=e;
    // Bounded, synchronous batches: no threads, locks or shutdown waits. Flush
    // each scheduler exit so a short user test leaves useful data immediately.
    if(used==128 || kind==2)flush();
    SetLastError(error);
}

// Preserve integer registers, flags, x87 stack/control and SSE/MXCSR. FNINIT
// allows callbacks while native code has live x87 temporaries or a full stack.
#define OBSERVE(kind) __asm { pushfd } __asm { pushad } \
    __asm { mov ebx,esp } __asm { sub esp,544 } __asm { and esp,0xfffffff0 } \
    __asm { fxsave [esp] } __asm { fninit } __asm { cld } __asm { push ebx } __asm { push kind } \
    __asm { call mm_ai_observe } __asm { add esp,8 } __asm { fxrstor [esp] } \
    __asm { mov esp,ebx } __asm { popad } __asm { popfd }

static unsigned return_begin=0x415c46,return_end=0x416520;
static unsigned return_model_begin=0x4766b7,return_model_end=0x476b30;
static unsigned eval1_yes=0x42867c,eval1_no=0x4288df;
static unsigned eval2_yes=0x42867c,eval2_no=0x4288dc;
static unsigned return_eligible=0x428756,return_again=0x4288c4;
static unsigned return_yield=0x42893f,return_commit=0x4289e5;
static unsigned return_execute=0x4164e3,retire_yes=0x428c54,retire_no=0x428e18;
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_begin_hook() {
    OBSERVE(1)
    __asm { push ebp }
    __asm { mov ebp,esp }
    __asm { sub esp,0x7c }
    __asm { jmp dword ptr [return_begin] }
}
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_end_hook() {
    OBSERVE(2)
    __asm { pop ebx }
    __asm { pop esi }
    __asm { mov esp,ebp }
    __asm { pop ebp }
    __asm { jmp dword ptr [return_end] }
}
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_model_begin_hook() {
    OBSERVE(3)
    __asm { push -1 }
    __asm { push 0x5bf7d1 }
    __asm { jmp dword ptr [return_model_begin] }
}
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_model_end_hook() {
    OBSERVE(4)
    __asm { pop edi }
    __asm { pop esi }
    __asm { pop ebp }
    __asm { pop ebx }
    __asm { add esp,0xcc }
    __asm { jmp dword ptr [return_model_end] }
}
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_eval1_hook() {
    OBSERVE(5)
    __asm { test al,al }
    __asm { jz no_result }
    __asm { jmp dword ptr [eval1_yes] }
no_result: __asm { jmp dword ptr [eval1_no] }
}
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_eval2_hook() {
    OBSERVE(6)
    __asm { test al,al }
    __asm { jnz has_result }
    __asm { jmp dword ptr [eval2_no] }
has_result: __asm { jmp dword ptr [eval2_yes] }
}
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_eligible_hook() {
    OBSERVE(7)
    __asm { mov al,[ebp+0x1c] }
    __asm { test al,al }
    __asm { jmp dword ptr [return_eligible] }
}
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_again_hook() {
    OBSERVE(8)
    __asm { mov eax,[esi+0x14] }
    __asm { mov ecx,[ebp-8] }
    __asm { jmp dword ptr [return_again] }
}
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_yield_hook() {
    OBSERVE(9)
    __asm { mov al,[ebp-1] }
    __asm { mov [esi+0x11fe1],ebx }
    __asm { jmp dword ptr [return_yield] }
}
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_commit_hook() {
    OBSERVE(10)
    __asm { sub esp,0x10 }
    __asm { push ebx }
    __asm { push esi }
    __asm { jmp dword ptr [return_commit] }
}
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_execute_hook() {
    OBSERVE(11)
    __asm { test al,al }
    __asm { sete cl }
    __asm { jmp dword ptr [return_execute] }
}
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_retire_hook() {
    OBSERVE(12)
    __asm { test bl,bl }
    __asm { jz keep_action }
    __asm { jmp dword ptr [retire_yes] }
keep_action: __asm { jmp dword ptr [retire_no] }
}
struct Hook { unsigned site;void* target;unsigned length;unsigned char bytes[10]; };
static Hook hooks[]={
    {0x415c40,mm_ai_begin_hook,6,{0x55,0x8b,0xec,0x83,0xec,0x7c}},
    {0x41651b,mm_ai_end_hook,5,{0x5b,0x5e,0x8b,0xe5,0x5d}},
    {0x4766b0,mm_ai_model_begin_hook,7,{0x6a,0xff,0x68,0xd1,0xf7,0x5b,0}},
    {0x476b26,mm_ai_model_end_hook,10,{0x5f,0x5e,0x5d,0x5b,0x81,0xc4,0xcc,0,0,0}},
    {0x428674,mm_ai_eval1_hook,8,{0x84,0xc0,0x0f,0x84,0x63,0x02,0,0}},
    {0x4288d4,mm_ai_eval2_hook,8,{0x84,0xc0,0x0f,0x85,0xa0,0xfd,0xff,0xff}},
    {0x428751,mm_ai_eligible_hook,5,{0x8a,0x45,0x1c,0x84,0xc0}},
    {0x4288be,mm_ai_again_hook,6,{0x8b,0x46,0x14,0x8b,0x4d,0xf8}},
    {0x428936,mm_ai_yield_hook,9,{0x8a,0x45,0xff,0x89,0x9e,0xe1,0x1f,1,0}},
    {0x4289e0,mm_ai_commit_hook,5,{0x83,0xec,0x10,0x53,0x56}},
    {0x4164de,mm_ai_execute_hook,5,{0x84,0xc0,0x0f,0x94,0xc1}},
    {0x428c4c,mm_ai_retire_hook,8,{0x84,0xdb,0x0f,0x84,0xc4,1,0,0}},
};

static bool identity() {
    if((unsigned)GetModuleHandleW(nullptr)!=0x400000)return false;
    wchar_t path[MAX_PATH];if(!GetModuleFileNameW(nullptr,path,MAX_PATH))return false;
    HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_EXISTING,0,nullptr);
    if(file==INVALID_HANDLE_VALUE)return false;
    BCRYPT_ALG_HANDLE alg=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    unsigned char digest[32],block[65536];DWORD count=0;bool okay=false;
    if(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)==0 &&
       BCryptCreateHash(alg,&hash,nullptr,0,nullptr,0,0)==0) {
        bool read_ok=true;
        while(true) {
            if(!ReadFile(file,block,sizeof(block),&count,nullptr)){read_ok=false;break;}
            if(!count)break;
            if(BCryptHashData(hash,block,count,0)!=0){read_ok=false;break;}
        }
        if(read_ok && BCryptFinishHash(hash,digest,sizeof(digest),0)==0) {
            char text[65];const char* digits="0123456789abcdef";
            for(unsigned i=0;i<32;i++){text[2*i]=digits[digest[i]>>4];text[2*i+1]=digits[digest[i]&15];}
            text[64]=0;okay=!strcmp(text,engine_sha);
        }
    }
    if(hash)BCryptDestroyHash(hash);if(alg)BCryptCloseAlgorithmProvider(alg,0);
    CloseHandle(file);return okay;
}
static bool initialize() {
    char setting[4]={};GetEnvironmentVariableA("MM_AI_TRACE",setting,sizeof(setting));
    if(strcmp(setting,"1"))return true;
    if(!identity() || !QueryPerformanceFrequency(&frequency))return false;
    for(const auto& h:hooks)if(memcmp((void*)h.site,h.bytes,h.length))return false;
    wchar_t directory[MAX_PATH],name[MAX_PATH];
    DWORD length=GetEnvironmentVariableW(L"MM_AI_TRACE_DIR",directory,MAX_PATH);
    if(!length || length>=MAX_PATH-12)return false;
    lstrcpyW(name,directory);lstrcatW(name,L"\\trace.bin");
    output=CreateFileW(name,GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(output==INVALID_HANDLE_VALUE)return false;
    struct Header { char magic[8];uint32_t version,size;char hash[64]; };
    Header header={{'M','M','_','A','I','1','1',0},1,sizeof(Event),{}};
    memcpy(header.hash,engine_sha,64);DWORD actual;
    if(!WriteFile(output,&header,sizeof(header),&actual,nullptr) || actual!=sizeof(header)) {
        CloseHandle(output);output=INVALID_HANDLE_VALUE;return false;
    }
    written=sizeof(header);
    // Preflight all pages before writing any hook; restore on failure. This DLL
    // is injected only by a fresh-launch diagnostic, never into an active battle.
    DWORD old[sizeof(hooks)/sizeof(hooks[0])]{};unsigned prepared=0;
    for(const auto& h:hooks) {
        if(!VirtualProtect((void*)h.site,h.length,PAGE_EXECUTE_READWRITE,&old[prepared]))break;
        prepared++;
    }
    if(prepared!=sizeof(hooks)/sizeof(hooks[0])) {
        for(unsigned i=0;i<prepared;i++){DWORD ignored;VirtualProtect((void*)hooks[i].site,hooks[i].length,old[i],&ignored);}
        CloseHandle(output);output=INVALID_HANDLE_VALUE;return false;
    }
    for(const auto& h:hooks) {
        unsigned char data[10];memset(data,0x90,sizeof(data));data[0]=0xe9;
        *(unsigned*)(data+1)=(unsigned)h.target-h.site-5;memcpy((void*)h.site,data,h.length);
        FlushInstructionCache(GetCurrentProcess(),(void*)h.site,h.length);
    }
    for(unsigned i=0;i<prepared;i++){DWORD ignored;VirtualProtect((void*)hooks[i].site,hooks[i].length,old[i],&ignored);}
    active=true;return true;
}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID) {
    if(reason==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(instance);return initialize()?TRUE:FALSE;}
    if(reason==DLL_PROCESS_DETACH){flush();if(output!=INVALID_HANDLE_VALUE)CloseHandle(output);}
    return TRUE;
}

#ifdef MM_AI_TEST
// Offline fixture only; absent from the shipped DLL.
extern "C" __declspec(dllexport) void __cdecl mm_ai_test_begin() {
    active=true;output=(HANDLE)0x1234;used=sequence=written=0;
    frequency.QuadPart=1000000;started[0].QuadPart=started[1].QuadPart=0;
}
extern "C" __declspec(dllexport) unsigned __cdecl mm_ai_test_count() { return used; }
extern "C" __declspec(dllexport) const Event* __cdecl mm_ai_test_events() { return events; }
extern "C" __declspec(dllexport) unsigned __cdecl mm_ai_test_active() { return active; }
extern "C" __declspec(dllexport) void __cdecl mm_ai_test_cap() { written=kMaxBytes; }
extern "C" __declspec(dllexport) __declspec(naked) void mm_ai_test_roundtrip() {
    OBSERVE(0)
    __asm { ret }
}
#endif
