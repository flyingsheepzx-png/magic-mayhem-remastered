#pragma once
// Native registry capacity and object index are verified on engine 42f2aac7.
namespace mm_surface {
template<class Pointer, class SetIndex>
unsigned compact(Pointer* table,unsigned count,Pointer removed,SetIndex set_index){
    unsigned used=0;
    for(unsigned i=0;i<count;++i){
        Pointer p=table[i];if(!p || p==removed)continue;
        bool duplicate=false;
        for(unsigned j=0;j<used;++j)if(table[j]==p){duplicate=true;break;}
        if(!duplicate){table[used]=p;set_index(p,used++);}
    }
    for(unsigned i=used;i<128;++i)table[i]=Pointer{};
    return used;
}
}
