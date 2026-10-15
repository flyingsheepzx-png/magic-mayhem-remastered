#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cassert>
#include <cstdio>
#include <cstring>
extern "C" bool mm_install_surface_lifecycle();
struct Com{void** table;};
unsigned releases;
ULONG WINAPI release(Com*){++releases;return 0;}
int main(){
    // Execute the exact hash-verified native Destroy bytes against mock COM
    // surfaces in this test process, never against a running game.
    auto mapped=VirtualAlloc((void*)0x20580000,0x10000,MEM_RESERVE|MEM_COMMIT,PAGE_EXECUTE_READWRITE);
    if(!mapped){MEMORY_BASIC_INFORMATION m{};VirtualQuery((void*)0x20580000,&m,sizeof(m));printf("mapping error %lu base %p allocation %p size %zu state %lx\n",GetLastError(),m.BaseAddress,m.AllocationBase,m.RegionSize,m.State);return 2;}
    assert(mapped==(void*)0x20580000);
    assert(VirtualAlloc((void*)0x206e0000,0x20000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE)==(void*)0x206e0000);
    FILE* f=nullptr;assert(!fopen_s(&f,"native_destroy.bin","rb"));
    assert(fread((void*)0x2058b3e0,1,0xd8,f)==0xd8);fclose(f);
    unsigned char create[]={0xa1,0x54,0x81,0x6f,0x20,0x33,0xc0,0xc2,0x0c,0};
    memcpy((void*)0x2058ad90,create,sizeof(create));
    assert(mm_install_surface_lifecycle());
    using Destroy=void(__thiscall*)(void*);auto destroy=(Destroy)0x2058b3e0;
    void* vt[39]{};vt[2]=(void*)release;Com com{vt};
    unsigned char dead[50]{},live[50]{},other[50]{};
    auto table=(void**)0x206f6950;auto count=(unsigned*)0x206f8154;
    // Reproduce the retained scene: table head with null surfaces, index44.
    *(unsigned*)(dead+0x1c)=44;table[0]=dead;table[1]=other;*count=2;
    destroy(dead);assert(*count==1 && table[0]==other && !table[1]);assert(!releases);
    // Stale live index and duplicate aliases must release exactly once.
    *(void**)(live+4)=&com;*(void**)(live+8)=&com;*(unsigned*)(live+0x1c)=44;
    table[0]=live;table[1]=other;table[2]=live;*count=3;
    destroy(live);assert(*count==1 && table[0]==other && !table[1]);
    assert(releases==2 && !*(void**)(live+4) && !*(void**)(live+8));
    destroy(live);assert(releases==2 && *count==1);
    // Actual save14 second-load shape: base alias null, queried alias live.
    // Native previously crashed at58b40b. Preserve the queried Release and
    // registry compaction, then permit repeated destruction without a release.
    *(void**)(live+8)=&com;*(unsigned*)(live+0x1c)=53;
    table[1]=live;table[2]=live;*count=3;
    destroy(live);assert(releases==3 && *count==1 && table[0]==other && !table[1]);
    assert(!*(void**)(live+4) && !*(void**)(live+8));
    destroy(live);assert(releases==3 && *count==1);
    // Repeated recreate/destroy cycles must not leak registry capacity.
    for(unsigned i=0;i<128;++i){
        *(void**)(live+8)=&com;table[1]=live;*count=2;
        *(unsigned*)(live+0x1c)=i;
        destroy(live);assert(*count==1 && table[0]==other && !table[1]);
    }
    assert(releases==131);
    // Palette ownership remains native even when the base alias is absent.
    *(void**)(live+8)=&com;*(void**)(live+0xc)=&com;table[1]=live;*count=2;
    destroy(live);assert(releases==133 && !*(void**)(live+0xc) && *count==1);
    destroy(other);assert(!*count && !table[0]);
    puts("exact native Destroy + lifecycle hooks passed; no duplicate COM Release");
}
