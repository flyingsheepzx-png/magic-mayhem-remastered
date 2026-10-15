// Single-player ground-walking continuity. Native safety/reservations run first.
#include <windows.h>
#include <string.h>
struct MomentumStart{void* unit;int speed,remainder,threshold,kind,direction,action,wait;bool redirect,applied;int turn;};
static MomentumStart starts[4096];
static void* redirect_unit;
static int mf(void* p,int off){return *(int*)((char*)p+off);}
static int& mw(void* p,int off){return *(int*)((char*)p+off);}
static MomentumStart* record(void* u){unsigned id=*(unsigned short*)u;return id<4096?&starts[id]:nullptr;}
extern "C" void __cdecl mm_momentum_redirect_begin(void* u){
    // Explicit transaction only; no time-based grace period after actual stop.
    redirect_unit=mf(u,0x5fc)==2 && mf(u,0x618)==1 && mf(u,0x66c)==0?u:nullptr;
}
extern "C" void __cdecl mm_momentum_redirect_end(){redirect_unit=nullptr;}
static void __cdecl momentum_capture(void* u){
    auto* s=record(u);if(!s)return;
    *s={u,mf(u,0xb63),mf(u,0xb6b),mf(u,0xb67),mf(u,0x610),mf(u,0x608),mf(u,0x5fc),mf(u,0x66c),redirect_unit==u,false,0};
}
static int __cdecl momentum_continue(void* u,int old_kind){
    auto* s=record(u);
    if(*(int*)0x6e1f0c>1 || !s || s->unit!=u || s->applied || s->speed<=0 || s->speed>1000000 ||
       s->threshold<=0 || s->remainder<0 || s->remainder>=s->threshold || s->wait || mf(u,0x66c) ||
       (s->action!=2 && !(s->redirect && s->action==15)) || mf(u,0x5fc)!=s->action ||
       mf(u,0x618)!=1 || mf(u,0x10c) || mf(u,0x104) ||
       *((char*)u+0x71c) || *((char*)u+0x723) || !mf(u,4) || !mf(u,0xe4) ||
       s->kind!=0 || old_kind!=s->kind || mf(u,0x610)!=s->kind ||
       mf((void*)mf(u,0xac),8)!=1 || mf((void*)mf(u,0xac),0x44)!=1)return 0;
    int threshold=mf(u,0xb67);if(threshold<=0)return 0;
    int delta=(mf(u,0x608)-s->direction+8)&7;int turn=delta>4?8-delta:delta;
    // Restore entry speed rather than the first native speed calculation:
    // the native calculation below the reset gate applies acceleration once.
    mw(u,0xb63)=s->speed;
    mw(u,0xb6b)=(int)((long long)s->remainder*threshold/s->threshold);
    s->applied=true;s->turn=turn;return 1;
}
static void __cdecl momentum_turn_limit(void* u,int desired){
    auto* s=record(u);if(!s || s->unit!=u || !s->applied || s->turn<2 || desired<=0)return;
    // Cap after native acceleration, using the new terrain-derived desired
    // speed. Otherwise acceleration could immediately undo the turn reduction.
    // Use terrain target, not last turn's already-reduced speed: repeated
    // corners must not compound geometrically into an unintended crawl.
    int base=desired;
    int eighths=s->turn==2?6:s->turn==3?5:4;
    int cap=(int)((long long)base*eighths/8);if(cap<1)cap=1;
    if(mf(u,0xb63)>cap)mw(u,0xb63)=cap;
}
static DWORD entry_resume=0x510e86,gate_resume=0x511446,gate_done=0x511471,finish_resume=0x511591;
__declspec(naked) static void momentum_entry_hook(){__asm{
    pushfd
    pushad
    push ecx
    call momentum_capture
    add esp,4
    popad
    popfd
    sub esp,30h
    push ebx
    push ebp
    push esi
    jmp dword ptr [entry_resume]
}}
__declspec(naked) static void momentum_gate_hook(){__asm{
    pushfd
    pushad
    mov eax,[esp+40h]
    push eax
    push esi
    call momentum_continue
    add esp,8
    test eax,eax
    jz native_gate
    popad
    popfd
    jmp dword ptr [gate_done]
native_gate:
    popad
    popfd
    je preserved
    cmp [esi+0b73h],ebp
    jmp dword ptr [gate_resume]
preserved:
    jmp dword ptr [gate_done]
}}
__declspec(naked) static void momentum_finish_hook(){__asm{
    pushfd
    pushad
    mov eax,[esp+50h]
    push eax
    push esi
    call momentum_turn_limit
    add esp,8
    popad
    popfd
    mov eax,[esi+10ch]
    jmp dword ptr [finish_resume]
}}
static bool mp(unsigned a,void* target,const unsigned char* expected,unsigned n){
    if(memcmp((void*)a,expected,n))return false;DWORD old;
    if(!VirtualProtect((void*)a,n,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char bytes[8];memset(bytes,0x90,n);bytes[0]=0xe9;*(DWORD*)(bytes+1)=(DWORD)target-a-5;
    memcpy((void*)a,bytes,n);FlushInstructionCache(GetCurrentProcess(),(void*)a,n);DWORD unused;VirtualProtect((void*)a,n,old,&unused);return true;
}
extern "C" bool __cdecl mm_install_movement_momentum(){
    const unsigned char entry[]={0x83,0xec,0x30,0x53,0x55,0x56};
    const unsigned char gate[]={0x74,0x31,0x39,0xae,0x73,0x0b,0,0};
    const unsigned char finish[]={0x8b,0x86,0x0c,0x01,0,0};
    if(memcmp((void*)0x510e80,entry,6)||memcmp((void*)0x51143e,gate,8)||memcmp((void*)0x51158b,finish,6))return false;
    return mp(0x510e80,(void*)momentum_entry_hook,entry,6)&&mp(0x51143e,(void*)momentum_gate_hook,gate,8)&&mp(0x51158b,(void*)momentum_finish_hook,finish,6);
}
