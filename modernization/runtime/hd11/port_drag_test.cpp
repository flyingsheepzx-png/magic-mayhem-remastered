// Execute the production wrapper with isolated memory and a native draw observer.
#include "port_drag.cpp"
#include <cassert>
#include <cstdio>
namespace {
int expected_scale,calls;
void __fastcall observe(void*,void*){
    const int expected[]={83,66,83,66};
    for(int i=0;i<4;i++)assert(((int*)0x5c774c)[i]==expected[i]*expected_scale);
    ++calls;
}
}
int main(){
    assert(VirtualAlloc((void*)0x5c0000,65536,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
    assert(VirtualAlloc((void*)0x640000,65536,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
    int table[]={83,66,83,66};memcpy((void*)0x5c774c,table,16);
    original=(Draw)observe;
    unsigned char a[0x30]{},b[0x30]{};*(unsigned*)a=0x5c6ee8;*(unsigned*)b=0x5c6f54;
    auto** controls=(unsigned char**)MM_HD_CONTROL_TABLE;controls[0]=a;controls[1]=b;
    // Empty controls: independent UI. Native combat controls: battle.
    for(int repeat=0;repeat<100;repeat++)for(int battle=0;battle<2;battle++){
        *(int*)MM_HD_CONTROL_COUNT=battle?2:0;expected_scale=battle?1:2;
        draw(nullptr,nullptr);assert(!memcmp((void*)0x5c774c,table,16));
    }
    assert(calls==200);puts("200 UI/battle draw calls: correct bounds and exact restoration");
}
