// Isolated v22 experiment. No map, route-buffer, or save writes.
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int g(unsigned a) { return *(int*)a; }
static int word(const void* p,int o) { return *(const int*)((const char*)p+o); }
typedef int (__thiscall *Space)(void*,int,int,int,void*);
typedef int (__thiscall *Edge)(void*,int,int,int,int,int,int,void*,int*,int);
static Space space=(Space)0x4f46b0;
static Space support=(Space)0x4f4330;
static Edge edge=(Edge)0x4f3990;
static unsigned continuation=0x4f4009, success=0x4f4191;
static unsigned accepts=0, rejects=0;
static bool logging=false;

struct P {int x,y,z;};
static bool inside(P p) {return p.x>=0&&p.y>=0&&p.z>=0&&p.x<g(0x6c5494)&&p.y<g(0x6c5498)&&p.z<g(0x6c549c);}
static const unsigned short* cell(P p) {return (const unsigned short*)(g(0x6c54dc)+12*(p.x+p.y*g(0x6c5494)+p.z*g(0x6c54a0)));}
static int height(P p) {unsigned id=cell(p)[0];return p.z*16+(id?g(g(0x65660c)+id*0x164+0x94):0);}
static bool terrain_surface(P p) {
    const unsigned short* c=cell(p); unsigned id=c[0];
    if (!id || (c[5]&(0x4000|0x80|0x30)) || c[1]!=0xffff) return false;
    int table=g(0x65660c)+id*0x164, h=g(table+0x94);
    return h>=0&&h<16&&(*(unsigned char*)(table+0xb0)&8);
}
static bool unoccupied(P p,void* profile) {
    // The exceptional side is not an endpoint: reject any occupant, including
    // reservations, at both its original and raised height.
    for(int k=0;k<word(profile,0)+1;k++) {
        P q={p.x,p.y,p.z+k};if(!inside(q))return false;
        const unsigned short* c=cell(q);
        if ((c[5]&3)&&c[2]!=0xffff)return false;
    }
    return true;
}
static bool native_edge(void* map,P a,P b,void* profile) {
    int kind=5;
    return edge(map,a.x,a.y,a.z,b.x,b.y,b.z,profile,&kind,-1)&&kind==0;
}
static void log_accept(P a,P b,P side,void* profile) {
    if(!logging || accepts>4000)return;
    FILE* f=nullptr;fopen_s(&f,"modernization\\logs\\terrain-diagonal.csv","a");
    if(f){fprintf(f,"%lu,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",GetTickCount(),a.x,a.y,a.z,b.x,b.y,b.z,side.x,side.y,side.z,word(profile,0),word(profile,0x11));fclose(f);}
}

// Called only after native endpoint/support/movement-mode checks passed and
// immediately before its conservative single-cell diagonal side-column test.
static int __cdecl try_half_stair(void* map,void* profile,const int* frame) {
    if(g(0x6e1f0c)>1 || word(profile,4)!=1 || word(profile,0)<1 || word(profile,0)>8 ||
       word(profile,8)!=0 || word(profile,12)!=1 || *(unsigned char*)((char*)profile+0x15))return 0;
    P a={frame[10],frame[11],frame[12]},b={frame[13],frame[14],frame[15]};
    if(abs(a.x-b.x)+abs(a.y-b.y)!=1 || abs(a.z-b.z)!=1 || !inside(a)||!inside(b))return 0;
    P low=a.z<b.z?a:b,high=a.z<b.z?b:a;
    // Half-height terrain stair to the adjacent full floor. Do not exempt
    // props, cliffs, diagonals, unsupported destinations or movement modes.
    if(!terrain_surface(low) || g(g(0x65660c)+cell(low)[0]*0x164+0x94)!=8 ||
       cell(high)[0]!=0 || abs(height(high)-height(low))!=8)return 0;
    P below={high.x,high.y,high.z-1};const unsigned short* floor=cell(below);
    if(!floor[0] || g(g(0x65660c)+floor[0]*0x164+0x94)!=16 ||
       !(*(unsigned char*)(g(0x65660c)+floor[0]*0x164+0xb0)&8) ||
       (floor[5]&(0x80|0x30)))return 0;
    // The native endpoints have already passed. Repeat them explicitly;
    // accept their actual headroom rather than a fictitious raised low column.
    return space(map,a.x,a.y,a.z,profile) && space(map,b.x,b.y,b.z,profile) &&
           support(map,a.x,a.y,a.z,profile) && support(map,b.x,b.y,b.z,profile);
}
static int __cdecl try_diagonal(void* map,void* profile,const int* frame) {
    if(try_half_stair(map,profile,frame))return 1;
    if(g(0x6e1f0c)>1 || word(profile,4)!=1 || word(profile,0)<1 || word(profile,0)>8 ||
       word(profile,8)!=0 || word(profile,12)!=1 || *(unsigned char*)((char*)profile+0x15))return 0;
    P a={frame[10],frame[11],frame[12]},b={frame[13],frame[14],frame[15]};
    if(a.z!=b.z||abs(a.x-b.x)!=1||abs(a.y-b.y)!=1||!inside(a)||!inside(b))return 0;
    P sides[2]={{a.x,b.y,a.z},{b.x,a.y,a.z}};
    int bad=-1;
    for(int j=0;j<2;j++)if(!space(map,sides[j].x,sides[j].y,sides[j].z,profile)){
        if(bad!=-1)return 0;bad=j;
    }
    if(bad<0)return 0;
    P low=sides[bad],raised={low.x,low.y,low.z+1};
    if(!inside(raised))return 0;
    const unsigned short* c=cell(low);
    // Only solid *subsurface*: props/solid tiles are never exempted.
    if(c[0]!=0 || !(c[5]&0x4000) || c[1]!=0xffff || (c[5]&0x30) ||
       !terrain_surface(a)||!terrain_surface(b)||!terrain_surface(raised))return 0;
    int ha=height(a),hb=height(b),hs=height(raised);
    if(abs(ha-hb)>8||hs<ha||hs<hb||hs-ha>16||hs-hb>16)return 0;
    if(!space(map,raised.x,raised.y,raised.z,profile)||!support(map,raised.x,raised.y,raised.z,profile)||
       !unoccupied(low,profile)||!native_edge(map,a,raised,profile)||!native_edge(map,raised,b,profile)||
       !native_edge(map,b,raised,profile)||!native_edge(map,raised,a,profile)){rejects++;return 0;}
    accepts++;log_accept(a,b,raised,profile);return 1;
}

extern "C" __declspec(dllexport) __declspec(naked) void terrain_hook() {__asm {
    pushfd
    pushad
    lea eax,[esp+36]
    push eax
    push esi
    push ebx
    call try_diagonal
    add esp,12
    test eax,eax
    jz original
    popad
    popfd
    jmp dword ptr [success]
original:
    popad
    popfd
    cmp dword ptr [esi+4],1
    jne accepted
    jmp dword ptr [continuation]
accepted:
    jmp dword ptr [success]
}}

BOOL WINAPI DllMain(HINSTANCE,DWORD reason,LPVOID) {
    if(reason!=DLL_PROCESS_ATTACH)return TRUE;
    // Normal play should not open a file on every accepted search edge.
    // Keep the diagnostic explicitly available for targeted investigations.
    char trace[4]={};GetEnvironmentVariableA("MM_TERRAIN_DIAGONAL_TRACE",trace,sizeof(trace));
    logging=trace[0]=='1' && trace[1]==0;
    unsigned char expected[]={0x83,0x7e,4,1,0x0f,0x85,0x88,1,0,0};
    void* site=(void*)0x4f3fff;
    if(memcmp(site,expected,sizeof(expected)))return FALSE;
    char disable[4]={};GetEnvironmentVariableA("MM_TERRAIN_DIAGONAL_DISABLE",disable,4);
    if(disable[0]=='1')return TRUE;
    DWORD old;if(!VirtualProtect(site,sizeof(expected),PAGE_EXECUTE_READWRITE,&old))return FALSE;
    unsigned char patch[10]={0xe9,0,0,0,0,0x90,0x90,0x90,0x90,0x90};
    *(int*)(patch+1)=(int)((char*)terrain_hook-(char*)site-5);memcpy(site,patch,10);
    FlushInstructionCache(GetCurrentProcess(),site,10);DWORD ignored;VirtualProtect(site,10,old,&ignored);
    return TRUE;
}
