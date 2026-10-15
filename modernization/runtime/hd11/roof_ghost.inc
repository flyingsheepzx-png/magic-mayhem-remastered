// Private body pass for native roof-clipped upper layers. No simulation or
// terrain command generation, selection mutation, or discovery of fogged units.
static Command roof_bodies[4096];
static int roof_owners[4096],roof_count;
static bool roof_readable(void* p,unsigned size){
    MEMORY_BASIC_INFORMATION m{};
    return p && VirtualQuery(p,&m,sizeof(m)) && m.State==MEM_COMMIT &&
        !(m.Protect&(PAGE_NOACCESS|PAGE_GUARD)) &&
        (uintptr_t)p+size>=(uintptr_t)p &&
        (uintptr_t)p+size<=(uintptr_t)m.BaseAddress+m.RegionSize;
}
static int roof_wrap_delta(int value,int center,int period){
    int d=value-center;if(d>period/2)d-=period;if(d<-period/2)d+=period;return d;
}
static void roof_collect(void* scene){
    roof_count=0;
    if(!captured || !occluded_units_enabled || g(0x6e1f0c)>1)return;
    int count=g(0x6def5c),width=g(0x6c5494),height=g(0x6c5498);
    auto* map=(unsigned char*)g(0x6c54dc);
    int player=g(0x644520),limit=f(scene,0x61),policy=f(scene,0x6d);
    if(policy!=0 && policy!=1)return;
    if(count<=0 || count>4096 || width<=0 || width>256 || height<=0 || height>256 ||
       !map || player<0 || player>7 || limit<0)return;
    int anchor[2];typedef void (__thiscall* AnchorFn)(void*,int*);
    ((AnchorFn)0x4f8230)(scene,anchor);
    int cx=f(scene,0x39),cy=f(scene,0x3d),radius=f(scene,0x5d),rot=f(scene,0x31)&3;
    int startx=cx+((rot==1 || rot==2)?radius:-radius);
    int starty=cy+((rot>=2)?radius:-radius);
    auto* units=(unsigned char*)g(0x6def58);
    if(!roof_readable(units,count*0xe4b))return;
    bool submitted[4096]{};
    for(int j=0;j<command_count;j++)if(body_commands[j] && owners[j]>=0 && owners[j]<count)submitted[owners[j]]=true;
    for(int i=0;i<count && roof_count<4096;i++){
        auto* unit=units+i*0xe4b;
        int x=f(unit,8),y=f(unit,12),z=f(unit,16);
        if(!f(unit,4) || !f(unit,0xe4) || !f(unit,0x24+player*4) ||
           x<0 || x>=width || y<0 || y>=height || z<0 || z>=32)continue;
        auto* tile=map+(g(0x6cb942+y*4)+g(0x6cb8c2+z*4)+x)*12;
        if(!roof_readable(tile,12) || (tile[11]&0x40) || (tile[8]&0x80))continue;
        bool hidden=policy==0?z>limit:
            ((tile[8]&3)>f(scene,0x65) && f(unit,0x108)<1);
        if(!hidden)continue;
        // A native body can still be submitted at a movement reservation tile.
        // Never duplicate it even when the current cell belongs to a hidden group.
        if(submitted[i])continue;
        // Respect native root-frame state and appearance modes. Do not create
        // an animation object for a unit that has none yet.
        bool alternate=f(unit,0x855)!=0;
        auto* anim=(unsigned char*)f(unit,alternate?0x829:0xb4);
        auto* appearance=(unsigned char*)f(unit,alternate?0x841:0xcc);
        auto* type=(unsigned char*)f(unit,0xac);
        auto* passes=(unsigned char*)f(unit,0xcf7);
        int pose=f(unit,0xbf3);
        if(!roof_readable(anim,16) || !roof_readable(appearance,0x114) ||
           !roof_readable(type,12) || !roof_readable(passes,720) || pose<0 || pose>=30)continue;
        auto* table=(int*)f(appearance,0x110);
        if(!roof_readable(table,16) || !roof_readable((void*)table[0],16))continue;
        unsigned frame=f(anim,4),total=f((void*)table[0],12);
        if(frame>total)frame=0;
        if(!roof_readable((void*)(table[2]+frame*4),4))continue;
        void* sprite=(void*)(g(table[2]+frame*4)+table[3]);
        if(!roof_readable(sprite,0x28) || f(sprite,4)<=0 || f(sprite,4)>1024 ||
           f(sprite,8)<=0 || f(sprite,8)>1024 || !f(sprite,0x1c) || f(sprite,0x1c)==-1)continue;
        int ox=f(anim,8),oy=f(anim,12);
        if(f(type,8)==2){
            if(rot==1){ox+=32;oy-=16;}else if(rot==2)oy-=32;else if(rot==3){ox-=32;oy-=16;}
        }
        int wx=cx*32+roof_wrap_delta(f(unit,0x14),cx*32,width*32)-startx*32+f(unit,0xb7b);
        int wy=cy*32+roof_wrap_delta(f(unit,0x18),cy*32,height*32)-starty*32+f(unit,0xb7f);
        int sx=0,sy=0;
        switch(rot){case 0:sx=wx-wy;sy=(wx+wy)/2;break;
          case 1:sx=wx+wy;sy=(wy-wx)/2;break;
          case 2:sx=wy-wx;sy=-(wx+wy)/2;break;
          case 3:sx=-wx-wy;sy=(wx-wy)/2;break;}
        int px=anchor[0]+sx+ox,py=anchor[1]+sy-f(unit,0x1c)+oy;
        if(px-f(sprite,12)>=clip[2] || py-f(sprite,16)>=clip[3] ||
           px-f(sprite,12)+f(sprite,4)<=clip[0] || py-f(sprite,16)+f(sprite,8)<=clip[1])continue;
        int shade=f(passes,600+pose*4);if(shade<-127)shade=-127;if(shade>127)shade=127;
        int palette=*(short*)(unit+0xcfb);if(palette<0 || palette>255)continue;
        for(int pass=0;pass<3 && roof_count<4096;pass++){
            int mode=f(passes,pose*4+pass*120);if(mode!=0 && mode!=31)continue;
            Command c{};f(&c,4)=(int)sprite;f(&c,8)=px;f(&c,12)=py;
            *(short*)(c.bytes+16)=(short)shade;*(short*)(c.bytes+18)=(short)palette;
            f(&c,24)=mode;*(short*)(c.bytes+28)=-30000;*(short*)(c.bytes+30)=-30000;
            roof_bodies[roof_count]=c;roof_owners[roof_count++]=i;
        }
    }
}
