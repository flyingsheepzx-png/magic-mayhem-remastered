// Native visual picking stays unchanged; fallback runs only on a movement click.
struct PickCell {int x,y,z;};
static PickCell pick_cells[128],pick_surfaces[128];
static int pick_surface_count,pick_anchor_x,pick_anchor_y,pick_mouse_x,pick_mouse_y,pick_rotation;
static int pick_count,pick_map,pick_scene;
static int pick_last_status,pick_last_raw[3],pick_last_replacement[3];
static int pg(unsigned a){return *reinterpret_cast<int*>(a);}
static int pf(void* p,unsigned n){return *reinterpret_cast<int*>(static_cast<unsigned char*>(p)+n);}
static void __cdecl pick_begin(void* scene){
    pick_count=0;pick_surface_count=0;pick_map=pg(0x6c54dc);pick_scene=reinterpret_cast<int>(scene);
}
static int __fastcall canopy_mask(void* sprite,int x,int y,int* point){
    typedef int (__fastcall* MaskFn)(void*,int,int,int*);
    int hit=((MaskFn)0x57dcf0)(sprite,x,y,point);
    auto* scene=reinterpret_cast<unsigned char*>(point)-0x91;
    if(reinterpret_cast<int>(scene)!=pick_scene || pg(0x6e1f0c)>1)return hit;
    PickCell cell{pf(scene,0x7d),pf(scene,0x81),pf(scene,0x85)};
    if(cell.x<0 || cell.x>=pg(0x6c5494) || cell.y<0 || cell.y>=pg(0x6c5498) || cell.z<0 || cell.z>=pg(0x6c549c))return hit;
    if(!hit)return hit;
    pick_anchor_x=x;pick_anchor_y=y;pick_mouse_x=point[0];pick_mouse_y=point[1];pick_rotation=pf(scene,0x31)&3;
    if(pick_count && !memcmp(&cell,&pick_cells[pick_count-1],12))return hit;
    if(pick_count==128){memmove(pick_cells,pick_cells+1,127*sizeof(PickCell));--pick_count;}
    pick_cells[pick_count++]=cell;return hit;
}
static unsigned pick_begin_resume=0x4f83f8;
__declspec(naked) void pick_begin_hook(){__asm{
    pushfd
    pushad
    push ecx
    call pick_begin
    add esp,4
    popad
    popfd
    sub esp,24h
    push ebx
    lea eax,[esp+20h]
    jmp dword ptr [pick_begin_resume]
}}
static bool pick_destination(PickCell raw,PickCell& goal){
    int w=pg(0x6c5494),h=pg(0x6c5498),l=pg(0x6c549c);
    if(w<1 || w>256 || h<1 || h>256 || l<1 || l>64 || raw.x<0 || raw.x>=w || raw.y<0 || raw.y>=h || raw.z<0 || raw.z>=l)return false;
    auto* tile=reinterpret_cast<unsigned char*>(pg(0x6c54dc))+12*(raw.x+w*(raw.y+h*raw.z));
    if(!readable(tile,12) || (tile[11]&0x40) || (tile[8]&0x80))return false;
    auto* type=reinterpret_cast<unsigned char*>(pg(0x65660c))+*reinterpret_cast<unsigned short*>(tile)*0x164;
    if(!readable(type,0x164))return false;
    goal=raw;if(pf(type,0x94)==16)++goal.z;
    return goal.z<l;
}
static bool pick_edge(void* unit,PickCell from,PickCell to){
    typedef int (__thiscall* TransitionFn)(void*,int,int,int,int,int,int,int*,int);
    int kind=5;
    return ((TransitionFn)0x514360)(unit,from.x,from.y,from.z,to.x,to.y,to.z,&kind,0) && kind==0;
}
// Three-valued bounded search: 1 reachable, 0 proven unreachable, -1 unknown.
// Native transition rules decide passability; search exhaustion is unknown.
static int pick_reachable(void* unit,PickCell goal,int& budget){
    int w=pg(0x6c5494),h=pg(0x6c5498),layers=pg(0x6c549c);
    PickCell start{pf(unit,8),pf(unit,12),pf(unit,16)};
    if(!memcmp(&start,&goal,12))return 1;
    if(start.x<0||start.x>=w||start.y<0||start.y>=h||start.z<0||start.z>=layers)return -1;
    bool incoming=false;
    for(int dx=-1;dx<=1&&!incoming;dx++)for(int dy=-1;dy<=1&&!incoming;dy++){
        if(!dx&&!dy)continue;
        for(int z=max(0,goal.z-1);z<=min(layers-1,goal.z+1)&&!incoming;z++){
            if(budget<=0)return -1;--budget;
            incoming=pick_edge(unit,{(goal.x+dx+w)%w,(goal.y+dy+h)%h,z},goal);
        }
    }
    if(!incoming)return 0;
    struct Node{PickCell p;int g,heap;};
    static Node nodes[4096];static int slots[8192],heap[4096];
    int count=1,nheap=1;memset(slots,0xff,sizeof slots);nodes[0]={start,0,0};heap[0]=0;
    auto key=[&](PickCell p){return p.x+w*(p.y+h*p.z);};
    auto slot=[&](PickCell p){int k=key(p);unsigned s=(static_cast<unsigned>(k)*2654435761u)&8191;while(slots[s]>=0&&key(nodes[slots[s]].p)!=k)s=(s+1)&8191;return s;};
    auto score=[&](int i){int dx=abs(goal.x-nodes[i].p.x),dy=abs(goal.y-nodes[i].p.y);dx=min(dx,w-dx);dy=min(dy,h-dy);return nodes[i].g+10*max(dx,dy)+4*min(dx,dy);};
    slots[slot(start)]=0;
    auto lift=[&](int i){int pos=nodes[i].heap;while(pos>0){int parent=(pos-1)/2;if(score(i)>=score(heap[parent]))break;heap[pos]=heap[parent];nodes[heap[pos]].heap=pos;pos=parent;}heap[pos]=i;nodes[i].heap=pos;};
    while(nheap){
        int current=heap[0],last=heap[--nheap];if(nheap){int pos=0;while(pos*2+1<nheap){int child=pos*2+1;if(child+1<nheap&&score(heap[child+1])<score(heap[child]))++child;if(score(last)<=score(heap[child]))break;heap[pos]=heap[child];nodes[heap[pos]].heap=pos;pos=child;}heap[pos]=last;nodes[last].heap=pos;}
        nodes[current].heap=-1;Node from=nodes[current];if(!memcmp(&from.p,&goal,12))return 1;
        for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy){if(!dx&&!dy)continue;
            for(int z=max(0,from.p.z-1);z<=min(layers-1,from.p.z+1);++z){
                PickCell next{(from.p.x+dx+w)%w,(from.p.y+dy+h)%h,z};
                int cost=from.g+(dx&&dy?14:10);unsigned s=slot(next);int index=slots[s];
                if(index>=0 && nodes[index].g<=cost)continue;
                if(budget<=0)return -1;--budget;if(!pick_edge(unit,from.p,next))continue;
                if(index<0){if(count==4096)return -1;index=count++;slots[s]=index;nodes[index]={next,cost,nheap};heap[nheap++]=index;}
                else {nodes[index].g=cost;if(nodes[index].heap<0){nodes[index].heap=nheap;heap[nheap++]=index;}}
                lift(index);
            }
        }
    }
    return 0;
}
static void __cdecl pick_movement_fallback(unsigned flags){
    pick_last_status=0;
    if(!(flags&4) || pg(0x6903e8)!=1 || pg(0x6e1f0c)>1 || pg(0x6a5134)!=1 || pick_count<1 || pick_map!=pg(0x6c54dc))return;
    // Shift/Alt/Ctrl retain native force-attack, item and selection semantics.
    if((GetKeyState(VK_CONTROL)|GetKeyState(VK_MENU)|GetKeyState(VK_SHIFT))&0x8000)return;
    PickCell raw{pg(0x6c5488),pg(0x6c5484),pg(0x6cbb64)},goal{};
    memcpy(pick_last_raw,&raw,12);
    if(memcmp(&raw,&pick_cells[pick_count-1],12) || !pick_destination(raw,goal))return;
    int count=pg(0x6def5c),player=pg(0x644520);auto* units=reinterpret_cast<unsigned char*>(pg(0x6def58));
    if(count<1 || count>4096 || player<0 || player>7 || !readable(units,count*0xe4b))return;
    void* selected[32];int selected_count=0;
    for(int i=0;i<count;++i){auto* u=units+i*0xe4b;if(!pf(u,4)||!pf(u,0xe4)||!pf(u,0x68)||pf(u,0x174)!=player)continue;
        auto* type=reinterpret_cast<void*>(pf(u,0xac));
        if(!readable(type,0x48)||pf(type,8)!=1||pf(type,0x44)!=1||pf(u,0x104)||pf(u,0x10c)||u[0x71c]||u[0x723])return;
        if(selected_count==32)return;selected[selected_count++]=u;
    }
    if(!selected_count)return;
    int budget=24000;
    for(int i=0;i<selected_count;++i){
        int result=pick_reachable(selected[i],goal,budget);pick_last_status=result==0?1:result==1?2:3;
        if(result!=0)return;
    }
    // Reachability does not identify a screen pixel. Never prefer a lower
    // same-column floor unless its projected top surface contains the click.
    pick_surface_count=0;
    int width=pg(0x6c5494),height=pg(0x6c5498);
    for(int z=raw.z-1;z>=0 && raw.z-z<=32;--z){
        int px=pick_mouse_x-pick_anchor_x;
        // Native4f83f0 traverses its current picker/map axes with X(+32,+16)
        // and Y(-32,+16), including after view rotation. Applying camera
        // rotation again here mixes picker space with unrotated world space.
        // Full support height16 means standing/top plane is z+1, not z-1.
        int py=2*(pick_mouse_y-pick_anchor_y+16*(z+1-raw.z));
        int dx=py+px,dy=py-px;
        int bx=(dx>=0?dx:dx-63)/64,by=(dy>=0?dy:dy-63)/64;
        for(int ix=bx;ix<=bx+1;++ix)for(int iy=by;iy<=by+1;++iy){
            // A screen diamond becomes a square in inverse grid coordinates.
            // Half-open ownership prevents overlap and ambiguous edge choices.
            int ux=dx-ix*64,uy=dy-iy*64;
            if(ux<-32 || ux>=32 || uy<-32 || uy>=32)continue;
            PickCell candidate{(raw.x+ix+width*4)%width,(raw.y+iy+height*4)%height,z},target{};
            if(pick_destination(candidate,target) && target.z==z+1 && pick_surface_count<128)pick_surfaces[pick_surface_count++]=candidate;
        }
    }
    // Candidates were accumulated high-to-low; prefer the highest reachable floor.
    for(int i=0;i<pick_surface_count;++i){
        PickCell candidate=pick_surfaces[i],target{};
        if(candidate.z>=raw.z || !pick_destination(candidate,target))continue;
        bool reachable=true;
        for(int j=0;j<selected_count;++j)if(pick_reachable(selected[j],target,budget)!=1){reachable=false;break;}
        if(!reachable)continue;
        *reinterpret_cast<int*>(0x6c5488)=candidate.x;*reinterpret_cast<int*>(0x6c5484)=candidate.y;*reinterpret_cast<int*>(0x6cbb64)=candidate.z;
        typedef int (__cdecl* CursorFn)();*reinterpret_cast<int*>(0x5e04c8)=((CursorFn)0x4a3c70)();
        memcpy(pick_last_replacement,&candidate,12);pick_last_status=6;return;
    }
    // Frontmost reachable layer actually hit at this same pixel. No snapping
    // to neighboring cells and no passing movement through collision geometry.
    for(int i=pick_count-2,attempts=0;i>=0 && attempts<12;--i){
        PickCell candidate=pick_cells[i],target{};
        if(candidate.z>raw.z || !pick_destination(candidate,target))continue;
        if(!memcmp(&candidate,&raw,12))continue;++attempts;
        bool reachable=true;
        for(int j=0;j<selected_count;++j)if(pick_reachable(selected[j],target,budget)!=1){reachable=false;break;}
        if(!reachable)continue;
        *reinterpret_cast<int*>(0x6c5488)=candidate.x;*reinterpret_cast<int*>(0x6c5484)=candidate.y;*reinterpret_cast<int*>(0x6cbb64)=candidate.z;
        typedef int (__cdecl* CursorFn)();*reinterpret_cast<int*>(0x5e04c8)=((CursorFn)0x4a3c70)();
        memcpy(pick_last_replacement,&candidate,12);pick_last_status=4;return;
    }
}
static bool install_canopy_pick(){
    static const unsigned sites[]={0x4f8aee,0x4f8b26,0x4f8b5e};
    const unsigned char begin[]={0x83,0xec,0x24,0x53,0x8d,0x44,0x24,0x20};
    if(memcmp(reinterpret_cast<void*>(0x4f83f0),begin,8))return false;
    for(auto a:sites){auto* p=reinterpret_cast<unsigned char*>(a);if(p[0]!=0xe8 || a+5+*reinterpret_cast<int*>(p+1)!=0x57dcf0)return false;}
    DWORD old=0,unused=0;auto* entry=reinterpret_cast<unsigned char*>(0x4f83f0);
    if(!VirtualProtect(entry,8,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char patch[]={0xe9,0,0,0,0,0x90,0x90,0x90};*reinterpret_cast<int*>(patch+1)=static_cast<int>(reinterpret_cast<uintptr_t>(pick_begin_hook)-0x4f83f0-5);
    memcpy(entry,patch,8);FlushInstructionCache(GetCurrentProcess(),entry,8);VirtualProtect(entry,8,old,&unused);
    for(auto a:sites){auto* p=reinterpret_cast<unsigned char*>(a);if(!VirtualProtect(p,5,PAGE_EXECUTE_READWRITE,&old))return false;
        *reinterpret_cast<int*>(p+1)=static_cast<int>(reinterpret_cast<uintptr_t>(canopy_mask)-a-5);
        FlushInstructionCache(GetCurrentProcess(),p,5);VirtualProtect(p,5,old,&unused);
    }
    return true;
}
