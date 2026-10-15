// Bounded native direct-route attempt BEFORE macro navigation picks a waypoint.
// Included in the verified 1.1 repath source; ordinary single-player walkers.
typedef int (__thiscall *DirectRouteFn)(void*,int,int,int,int*);
static int __cdecl short_direct_route(void* u,const unsigned* stack) {
    if(global(0x6e1f0c)>1 || global(0x6df184)!=0 ||
       !field(u,4) || !field(u,0xe4) || field(u,0x5ec)!=2 ||
       field(u,0x618)!=0 || field(u,0x104)!=0 || field(u,0x10c)!=0 ||
       *(unsigned char*)((char*)u+0x71c) || *(unsigned char*)((char*)u+0x723))return 0;
    void* type=*(void**)((char*)u+0xac);
    if(!type || field(type,8)!=1 || field(type,0x44)!=1)return 0;
    int x=(int)stack[0x2c0/4],y=(int)stack[0x2c4/4],z=(int)stack[0x2c8/4];
    int ax=field(u,8),ay=field(u,12),az=field(u,16);
    int w=global(0x6c5494),h=global(0x6c5498),layers=global(0x6c549c);
    if(x<0 || x>=w || y<0 || y>=h || z<0 || z>=layers ||
       ax<0 || ax>=w || ay<0 || ay>=h || az!=z)return 0;
    int length=max(abs(x-ax),abs(y-ay));
    if(length<1 || length>16 || abs(x-ax)>w/2 || abs(y-ay)>h/2)return 0;
    int route[0x83];
    if(!((DirectRouteFn)0x513370)(u,x,y,z,route) || route[3]!=0 ||
       route[4]!=length || route[0]!=x || route[1]!=y || route[2]!=z)return 0;
    for(int i=0;i<length;i++) {
        const int* p=route+5+i*7;
        // Keep flat ordinary walking, including independent occupancy checks.
        // Native owns waypoint direction/metadata; do not synthesize them.
        if(p[2]!=z || p[4]!=0 || p[5]!=0 || p[6]!=0 ||
           !walking_edge(u,ax,ay,az,p[0],p[1],p[2]))return 0;
        ax=p[0];ay=p[1];az=p[2];
    }
    if(ax!=x || ay!=y || az!=z)return 0;
    memcpy((void*)0x6c4bd0,route,sizeof(route));
    // Finished direct route no longer needs macro waypoint truncation/override.
    field(u,0xd03)=0;
    *(int*)0x6df184=0;
    return 1;
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
