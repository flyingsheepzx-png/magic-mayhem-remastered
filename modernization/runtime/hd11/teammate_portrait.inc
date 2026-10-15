// Native teammate wizard portraits (0x5c5c2c, target at control+0x89)
// consume mouse flags before the world handler. Keep selection outside targeting.
constexpr unsigned char teammate_original[]={0x8a,0x44,0x24,0x04,0x81,0xec,0x00,0x02,0x00,0x00};
int __cdecl teammate_mouse(unsigned char* control,unsigned flags){
    if(*reinterpret_cast<int*>(0x6e1f0c)>1 ||
       *reinterpret_cast<int*>(0x6903e8)!=2 || !(flags&15))return 0;
    auto* caster=*reinterpret_cast<unsigned char**>(0x6a2dd0+0x18ec);
    if(!readable(caster,0x5ec))return 0;
    int pending=*reinterpret_cast<int*>(caster+0x5e8);
    if(pending<0 || pending>=30)return 0;
    reset_spell_double_press();
    if(flags&12){
        // Consume down; cancel on release, so neither invokes native right-cast.
        if(flags&8){
            typedef void (__thiscall* PendingFn)(void*,int);
            ((PendingFn)0x509bd0)(caster,-1);
        }
        return 1;
    }
    if(!(flags&2))return 1; // Left down must not change the caster selection.
    if(!readable(control,0x8d))return 1;
    auto* target=*reinterpret_cast<unsigned char**>(control+0x89);
    if(unit_index(target)>=1024 || !readable(target,0x5ec) ||
       !*reinterpret_cast<int*>(target+4) || !*reinterpret_cast<int*>(target+0xe4))return 1;
    typedef unsigned char (__thiscall* TargetCursorFn)(void*);
    if(((TargetCursorFn)0x57cf40)(target)!=5)return 1;
    // Query native target rules for THIS portrait. A stale world cursor must
    // never authorize a different or invalid target.
    auto* cursor=reinterpret_cast<int*>(0x5e04c8);int previous=*cursor;*cursor=5;
    typedef void (__thiscall* CastFn)(void*);
    ((CastFn)0x57ce70)(target);
    *cursor=previous;
    return 1;
}
unsigned teammate_resume=0x46303a;
__declspec(naked) void teammate_mouse_hook(){__asm{
    pushfd
    pushad
    mov eax,[esp+28h]
    push eax
    push ecx
    call teammate_mouse
    add esp,8
    mov [esp+1ch],eax
    popad
    popfd
    test eax,eax
    jz native_teammate
    xor eax,eax
    ret 2ch
native_teammate:
    mov al,[esp+4]
    sub esp,200h
    jmp dword ptr [teammate_resume]
}}
