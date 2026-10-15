#include <cassert>
#include <cstdio>
#include "surface_registry.h"
struct Object{unsigned index;};
int main(){
    Object a{44},b{1},c{2};Object* t[128]={&a,&b,&c,&a};
    auto index=[](Object* p,unsigned i){p->index=i;};
    unsigned n=mm_surface::compact(t,4,&a,index);
    assert(n==2 && t[0]==&b && t[1]==&c && !t[2]);
    assert(b.index==0 && c.index==1);
    // Recreating one object repeatedly never leaves another registry alias.
    for(unsigned i=0;i<1000;++i){
        t[n++]=&a;a.index=n-1;
        n=mm_surface::compact(t,n,&a,index);
        assert(n==2 && t[0]==&b && t[1]==&c && !t[2]);
    }
    t[2]=&b;t[3]=nullptr;t[4]=&c;
    n=mm_surface::compact(t,5,(Object*)nullptr,index);assert(n==2);
    Object full[128]{};for(unsigned i=0;i<128;++i)t[i]=&full[i];
    n=mm_surface::compact(t,128,&full[0],index);assert(n==127);
    for(unsigned i=0;i<n;++i)assert(t[i]==&full[i+1] && t[i]->index==i);
    assert(!t[127]);puts("surface registry regressions passed");
}
