// Bounded native direct-route attempt BEFORE macro navigation picks a waypoint.
// Included in the verified 1.1 repath source; ordinary single-player walkers.
typedef int (__thiscall *DirectRouteFn)(void*,int,int,int,int*);
static bool corridor_route(void*,int,int,int,int*);
static bool local_route(void*,int,int,int,int*);
static bool long_route(void*,int,int,int,int*);
static int __cdecl short_direct_route(void* u,const unsigned* stack) {
 if(global(0x6df184)!=0 || field(u,0x618)!=0)return 0;
 int route[0x83];
 if(!corridor_route(u,(int)stack[0x2c0/4],(int)stack[0x2c4/4],(int)stack[0x2c8/4],route) &&
    !local_route(u,(int)stack[0x2c0/4],(int)stack[0x2c4/4],(int)stack[0x2c8/4],route) &&
    !long_route(u,(int)stack[0x2c0/4],(int)stack[0x2c4/4],(int)stack[0x2c8/4],route))return 0;
 memcpy((void*)0x6c4bd0,route,sizeof(route));field(u,0xd03)=0;return 1;
}
__declspec(naked) static void short_direct_hook() {
    __asm {
        pushfd
        pushad
        lea eax,[esp+24h]
        push eax
        push ebp
        call short_direct_route
        add esp,8
        test eax,eax
        jz native_macro_route
        popad
        popfd
        xor edx,edx
        push 5132ach
        ret
    native_macro_route:
        popad
        popfd
        mov ecx,[esp+2c4h]
        push 512936h
        ret
    }
}
