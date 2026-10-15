// Hash-gated single-player redirect. Same-layer, single-cell creatures only.
#include <windows.h>
#include <stdint.h>
#include <math.h>
#include <string.h>
#include <stdio.h>
#ifdef MM_COMBINED
extern "C" void __cdecl mm_render_tag(int*,void*);
extern "C" BOOL __cdecl mm_render_initialize();
extern "C" void __cdecl mm_render_forget_unit(void*);
#ifdef MM_ALL_IN_ONE
extern "C" BOOL __cdecl mm_clock_initialize(HINSTANCE);
extern "C" BOOL __cdecl mm_logic_time_initialize(HINSTANCE);
extern "C" BOOL __cdecl mm_game_time_initialize(HINSTANCE);
#endif
#endif

static int& field(void* u, unsigned off) { return *(int*)((char*)u + off); }
static int global(unsigned a) { return *(int*)a; }
typedef void (__thiscall *CellFn)(void*, int, int, int);
typedef void (__thiscall *UnitFn)(void*);
typedef void (__thiscall *ActionFn)(void*, int);
typedef int (__thiscall *ClearFn)(void*, int, int, int, int, int, int);
typedef int (__thiscall *BlockedFn)(void*, int, int, int);
typedef void (__thiscall *PlannerFn)(void*, void*, int, int, int, int, int*);
typedef int (__thiscall *TransitionFn)(void*,int,int,int,int,int,int,int*,int);
struct CellBackup { char* address; char value[12]; };

static void* unit;
static int cursor, ax, ay, px, py, tx, ty, pz, tz;
static double progress, scale;
static int native_root_x,native_root_y;
static bool animation_motion_trial;
static bool layer_redirect_trial;
static bool custom;
struct RedirectState {
    void* identity;
    int id,cursor,ax,ay,px,py,tx,ty,pz,tz,native_root_x,native_root_y;
    double progress,scale;
    bool custom;
};
static RedirectState redirect_states[1024];
struct BlockedWait {
    void* identity;
    int id,cursor,last_timer,retry_cooldown;
    int origin[3],next[3],goal[3];
    bool armed;
};
static BlockedWait blocked_waits[1024];
static int state_index(void* u) {
    uintptr_t base=(uintptr_t)global(0x6def58),p=(uintptr_t)u;
    int capacity=global(0x6def5c);
    if (!base || capacity<=0 || capacity>1024 || p<base ||
        p>=base+(uintptr_t)capacity*0xe4b || (p-base)%0xe4b) return -1;
    return (int)((p-base)/0xe4b);
}
static void load_state(void* u,int index) {
    RedirectState& s=redirect_states[index];
    if (s.identity!=u || s.id!=field(u,0)) {
        memset(&s,0,sizeof(s));s.identity=u;s.id=field(u,0);
    }
    unit=u;cursor=s.cursor;ax=s.ax;ay=s.ay;px=s.px;py=s.py;
    tx=s.tx;ty=s.ty;pz=s.pz;tz=s.tz;progress=s.progress;scale=s.scale;
    native_root_x=s.native_root_x;native_root_y=s.native_root_y;custom=s.custom;
}
static void save_state(int index) {
    RedirectState& s=redirect_states[index];
    s.cursor=cursor;s.ax=ax;s.ay=ay;s.px=px;s.py=py;s.tx=tx;s.ty=ty;
    s.pz=pz;s.tz=tz;s.progress=progress;s.scale=scale;
    s.native_root_x=native_root_x;s.native_root_y=native_root_y;s.custom=custom;
}
// The native reset and deserialize routines can reuse both pointer and unit ID.
// Invalidate before they change the object, without touching native/save data.
static void long_route_forget(void*);
static void __cdecl on_unit_replaced(void* u) {
    long_route_forget(u);
    int index=state_index(u);
    if(index<0)return;
    memset(&redirect_states[index],0,sizeof(redirect_states[index]));
    memset(&blocked_waits[index],0,sizeof(blocked_waits[index]));
    if(unit==u){unit=0;custom=false;}
#ifdef MM_COMBINED
    mm_render_forget_unit(u);
#endif
}
static bool force_rollback;
static bool disable_redirect;
static HANDLE logfile = INVALID_HANDLE_VALUE;
static int last_actor_x,last_actor_y;
static bool have_actor_queue;
struct TerrainSample { unsigned key_a,key_b; int x,y; };
static TerrainSample terrain_prev[512],terrain_now[512];
static int terrain_prev_count,terrain_now_count;
static int actor_world_x,actor_world_y,actor_height,actor_camera_x,actor_camera_y,
           actor_camera_z,actor_frame_origin_x,actor_frame_origin_y;
static int median_int(int* values,int count) {
    for (int i=1;i<count;i++) { int value=values[i],j=i;
        while (j>0 && values[j-1]>value) {values[j]=values[j-1];j--;}
        values[j]=value;
    }
    return values[count/2];
}

static void log_event(const char* reason, void* u, int x=0, int y=0) {
    if (logfile==INVALID_HANDLE_VALUE) return;
    char line[256]; DWORD n; LARGE_INTEGER q;
    QueryPerformanceCounter(&q);
    int len = _snprintf(line, sizeof(line), "%I64d,%s,%d,%d,%d,%d,%d,%d,%d,%d\r\n",
        q.QuadPart, reason, field(u,8),field(u,12),field(u,16),
        field(u,0x14),field(u,0x18),field(u,0xb3f),x,y);
    if (logfile != INVALID_HANDLE_VALUE && len>0) WriteFile(logfile,line,len,&n,0);
}

static bool clear(void* u, int x, int y, int z) {
    if (x<0 || y<0 || z<0 || x>=global(0x6c5494) || y>=global(0x6c5498) || z>=global(0x6c549c)) return false;
    void* type=*(void**)((char*)u+0xac);
    return !((ClearFn)0x4f13f0)((void*)0x6c5490,x,y,z,field(type,8),field(type,12),field(u,0))
        && !((BlockedFn)0x522f50)(u,x,y,z);
}

// 0x5111b9..0x51120e passes six canonical one-dword coordinate
// wrappers, an output movement kind and false to this native validator.
static bool walking_edge(void* u,int x,int y,int z,int dx,int dy,int dz) {
    if (abs(dx-x)>1 || abs(dy-y)>1 || abs(dz-z)>1 || !clear(u,dx,dy,dz)) return false;
    int kind=5;
    return ((TransitionFn)0x514360)(u,x,y,z,dx,dy,dz,&kind,0) && kind==0;
}

#include "short_direct_route.inc"
#include "corridor_route.inc"
#include "local_route.inc"
#include "long_route.inc"
static bool ordinary_wait(void* u) {
    if(global(0x6e1f0c)>1 || !field(u,4) || !field(u,0xe4) ||
       field(u,0x5ec)!=2 || field(u,0x5fc)!=15 || field(u,0x618)!=0 ||
       field(u,0x104)!=0 || field(u,0x10c)!=0 ||
       *(unsigned char*)((char*)u+0x71c) || *(unsigned char*)((char*)u+0x723))return false;
    void* type=*(void**)((char*)u+0xac);
    return type && field(type,8)==1 && field(type,0x44)==1;
}
#include "dynamic_wait.inc"
static void __cdecl remember_blocked_wait(void* u) {
    int index=state_index(u);if(index<0)return;
    BlockedWait& s=blocked_waits[index];s.armed=false;
    if(!ordinary_wait(u))return;
    int c=field(u,0x977),count=field(u,0x97b);
    if(c<0 || c>=count || count>16)return;
    if(s.identity!=u || s.id!=field(u,0) ||
       memcmp(s.origin,(char*)u+8,12) || memcmp(s.goal,(char*)u+0x96b,12))s.retry_cooldown=0;
    s.identity=u;s.id=field(u,0);s.cursor=c;s.last_timer=field(u,0x66c);
    memcpy(s.origin,(char*)u+8,12);
    memcpy(s.next,(char*)u+0x97f+c*28,12);
    memcpy(s.goal,(char*)u+0x96b,12);s.armed=true;
}
static void __cdecl wake_cleared_wait(void* u) {
    int index=state_index(u);if(index<0)return;
    BlockedWait& s=blocked_waits[index];if(!s.armed)return;
    int timer=field(u,0x66c),c=field(u,0x977),count=field(u,0x97b);
    if(!ordinary_wait(u) || s.identity!=u || s.id!=field(u,0) ||
       timer<=1 || timer>s.last_timer || c!=s.cursor || c<0 || c>=count || count>16 ||
       memcmp(s.origin,(char*)u+8,12) || memcmp(s.next,(char*)u+0x97f+c*28,12) ||
       memcmp(s.goal,(char*)u+0x96b,12)) {s.armed=false;return;}
    // Only shorten this recorded occupancy wait if its original walking edge
    // is now actually free. Native timer decrement then retries normally.
    s.last_timer=timer-1;
    if(walking_edge(u,s.origin[0],s.origin[1],s.origin[2],s.next[0],s.next[1],s.next[2])){
        field(u,0x66c)=1;s.armed=false;
    } else dynamic_wait_detour(u,s);
}

static bool slope_surface(void* u,int x,int y,int* surface_z,
                          int ax,int ay,int az,int bx,int by,int bz,int dx,int dy,int dz) {
    // A fourth swept cell needs native support AND walking connections on
    // both sides. Occupancy checks alone cannot distinguish castle floors.
    int found=-1;
    for (int z=min(az,min(bz,dz))-1;z<=max(az,max(bz,dz))+1;z++) {
        if (!clear(u,x,y,z)) continue;
        bool incoming=walking_edge(u,ax,ay,az,x,y,z) || walking_edge(u,bx,by,bz,x,y,z);
        if (!incoming || !walking_edge(u,x,y,z,dx,dy,dz)) continue;
        if (found!=-1) return false; // ambiguous overlapping supported floors
        found=z;
    }
    if (found<0) return false;
    *surface_z=found;
    log_event("validated_slope_surface",u,x,y);
    return true;
}

static void check_ownership(void* u,int x,int y,int z) {
    if (logfile==INVALID_HANDLE_VALUE) return;
    int w=global(0x6c5494),h=global(0x6c5498),layers=global(0x6c549c);
    if (w<=0 || h<=0 || layers<=0 || (uint64_t)w*h*layers>4000000) return;
    char* map=(char*)global(0x6c54dc);
    unsigned short id=(unsigned short)field(u,0);
    int owned=0,stray=0;
    void* type=*(void**)((char*)u+0xac);
    int height=field(type,12);
    for (int k=0;k<layers;k++) for (int j=0;j<h;j++) for (int i=0;i<w;i++) {
        char* cell=map+12*(i+j*w+k*w*h);
        if (*(unsigned short*)(cell+4)==id && (*(unsigned char*)(cell+10)&3)) {
            owned++;
            if (i!=x || j!=y || k<z || k>=z+height) stray++;
        }
    }
    log_event(stray || owned!=height?"occupancy_mismatch":"occupancy_ok",u,owned,stray);
}

static bool plan(void* u,int x,int y,int z,int* replacement,bool loaded=false,bool combat=false) {
    if(corridor_route(u,x,y,z,replacement) || local_route(u,x,y,z,replacement) || (!combat && long_route(u,x,y,z,replacement)))return true;
    if(loaded)return false;
    // A redirect has its own bounded search, not another unit's continuation.
    int allowance=global(0x5e174c);
    if (allowance<=0 || allowance>600) return false;
    *(unsigned char*)0x690354=1;
    ((PlannerFn)0x54b800)((void*)0x690148,u,field(u,0x694),x,y,z,&allowance);
    memcpy(replacement,(void*)0x690148,0x20c);
    return replacement[4]>0 && replacement[4]<=16 && replacement[3]==0;
}

static bool on_order_impl(void* u,bool loaded=false,bool combat=false) {
    if (global(0x6e1f0c)>1) return false;
    if (!field(u,4) || !field(u,0xe4) || field(u,0x618)!=1 || (!loaded && field(u,0xb6f)!=1)) return false;
    log_event("order_mid_segment",u,field(u,0x96b),field(u,0x96f));
    if (disable_redirect) return false;
    void* type=*(void**)((char*)u+0xac);
    if (field(type,8)!=1 || field(type,12)<1 || field(type,12)>8 || field(u,0x10c)!=0 ||
        *(unsigned char*)((char*)u+0x71c) || *(unsigned char*)((char*)u+0x723)) {
        log_event("fallback_movement_kind",u,field(type,8)*100+field(type,12),field(u,0x10c)); return false;
    }
    int old_cursor=field(u,0x977), count=field(u,0x97b);
    if (old_cursor<0 || old_cursor>=count || count>18) return false;
    int* oldpoint=(int*)((char*)u+0x97f+old_cursor*28);
    int z=field(u,16),originalx=field(u,8),originaly=field(u,12);
    int goalx=field(u,0x96b),goaly=field(u,0x96f),goalz=field(u,0x973);
    int oldx=oldpoint[0],oldy=oldpoint[1],oldz=oldpoint[2];
    int replacement[0x83];
    if (!plan(u,goalx,goaly,goalz,replacement,loaded,combat)) {
        log_event("fallback_no_route",u);return false;
    }
    int dx=replacement[5],dy=replacement[6],dz=replacement[7];
    log_event("old_edge",u,oldx,oldy);
    log_event("new_edge",u,dx,dy);
    log_event("edge_layers",u,oldz,dz);
    log_event("edge_kinds",u,replacement[10],replacement[11]);
    if (abs(dx-field(u,8))>1 || abs(dy-field(u,12))>1 ||
        (dx==field(u,8) && dy==field(u,12))) {log_event("fallback_first_step",u);return false;}
    if (dx==oldpoint[0] && dy==oldpoint[1] && dz==oldpoint[2]) {
        if(loaded){
            // Keep current segment reservation, animation and interpolation.
            // Replace only the continuation when the first edge is identical.
            memcpy(replacement+5,oldpoint,28);
            memcpy((char*)u+0x96b,replacement,sizeof(replacement));
            field(u,0xd03)=0;log_event("loaded_same_edge_route",u);
        }
        log_event("same_first_step",u);return false;
    }
    bool slope=oldz!=z || dz!=z || field(u,0xb57)!=0;
    if (slope && (!layer_redirect_trial || abs(oldz-z)>1 || abs(dz-z)>1)) {
        log_event("fallback_layer",u,oldz,dz);return false;
    }
    int startx=field(u,0x14),starty=field(u,0x18);
    int endx=dx*32,endy=dy*32;
    // Validate both anchor and swept cells. A->D remains a native route edge;
    // the current position must stay in the same verified flat layer.
    if (!clear(u,field(u,8),field(u,12),z)) {log_event("fallback_anchor_busy",u);return false;}
    int previous_x=-1,previous_y=-1;
    for (int i=0;i<=32;i++) {
        int x=(startx+(endx-startx)*i/32+16)/32;
        int y=(starty+(endy-starty)*i/32+16)/32;
        // Consecutive samples of a straight segment visit the same cell.
        // Validators are read-only; keep every distinct cell, including ends.
        if (x==previous_x && y==previous_y) continue;
        previous_x=x;previous_y=y;
        int surface_z=z;
        if (slope) {
            // Keep the swept footprint on the three cells belonging to
            // verified native old/new edges. Never infer another floor
            // merely from an interpolated world height.
            if (x==originalx && y==originaly) surface_z=z;
            else if (x==dx && y==dy) surface_z=dz;
            else if (x==oldx && y==oldy) surface_z=oldz;
            else if (!slope_surface(u,x,y,&surface_z,originalx,originaly,z,oldx,oldy,oldz,dx,dy,dz)) {
                log_event("fallback_slope_surface",u,x,y);return false;
            }
        }
        if (!clear(u,x,y,surface_z)) {log_event("fallback_sweep",u,x,y);return false;}
    }
    int anchorx=originalx,anchory=originaly;
    double full=sqrt((double)(endx-anchorx*32)*(endx-anchorx*32)+
                     (double)(endy-anchory*32)*(endy-anchory*32));
    double remaining=sqrt((double)(endx-startx)*(endx-startx)+(double)(endy-starty)*(endy-starty));
    if (remaining<1 || full<1) return false;
    int savex=field(u,0x14),savey=field(u,0x18),savez=field(u,0x1c);
    log_event("before_native_start",u,field(u,0xb7b),field(u,0xb7f));
    // Native start can refuse an edge after planning. Snapshot the current
    // unit and all cells its old/new one-cell footprint can touch, then
    // restore those bytes if it does not establish an active segment.
    unsigned char unit_before[0xe4b];
    memcpy(unit_before,u,sizeof(unit_before));
    CellBackup cells[900];int cell_count=0;
    int w=global(0x6c5494),h=global(0x6c5498),layers=global(0x6c549c);
    char* map=(char*)global(0x6c54dc);
    if (!map || w<=0 || h<=0 || layers<=0 || (uint64_t)w*h*layers>4000000) return false;
    const int cx[3]={originalx,oldx,dx},cy[3]={originaly,oldy,dy};
    for (int a=0;a<3;a++) for (int k=z-1;k<z+field(type,12)+1;k++)
        for (int j=cy[a]-2;j<=cy[a]+2;j++) for (int i=cx[a]-2;i<=cx[a]+2;i++) {
            if (i<0 || j<0 || k<0 || i>=w || j>=h || k>=layers) continue;
            if (cell_count>=900) return false;
            CellBackup& backup=cells[cell_count++];
            backup.address=map+12*(i+j*w+k*w*h);
            memcpy(backup.value,backup.address,12);
        }
    field(u,0x618)=0;field(u,0xb6f)=0;field(u,0x5f0)=0;
    field(u,0xb8b)=0;field(u,0x688)=0;field(u,0x694)=0;
    memcpy((char*)u+0x96b,replacement,sizeof(replacement));
    field(u,0xb8b)=1;field(u,0xd03)=0;
    ((ActionFn)0x50db60)(u,15);
    log_event("after_action",u,field(u,0xb7b),field(u,0xb7f));
    ((UnitFn)0x510e80)(u);
    log_event("after_native_start",u,field(u,0xb7b),field(u,0xb7f));
    int targetheight=field(u,0xb5f)+field(u,0xb57);
    // The native start owns D and sets animation/speed. Its first render must
    // retain P; only later movement updates interpolate P->D.
    field(u,0x14)=savex;field(u,0x18)=savey;field(u,0x1c)=savez;
    bool unsafe_slope=slope && (field(u,0x10c)!=0 || abs(targetheight-savez)>24);
    if (field(u,0x618)!=1 || force_rollback || unsafe_slope) {
        log_event(force_rollback?"forced_rollback":unsafe_slope?"unsafe_slope_rollback":"start_failed_rollback",u);
        for (int i=cell_count-1;i>=0;i--) memcpy(cells[i].address,cells[i].value,12);
        memcpy(u,unit_before,sizeof(unit_before));
        return false;
    }
    // The old B reservation remains valid until native start has reserved D.
    // Clear B only after start succeeds, avoiding an unowned failure state.
    ((CellFn)0x5093e0)(u,oldx,oldy,oldz);
    unit=u;cursor=field(u,0x977);ax=field(u,8)*32;ay=field(u,12)*32;
    px=startx;py=starty;tx=endx;ty=endy;pz=savez;tz=targetheight;progress=0;scale=full/remaining;
    field(u,0xb3f)=0;field(u,0xb47)=(px-ax)*6;field(u,0xb4b)=(py-ay)*6;
    custom=true;
    native_root_x=native_root_y=0;
    log_event("redirect",u,dx,dy);
    if (slope) log_event("redirect_slope",u,oldz,dz);
    check_ownership(u,dx,dy,dz);
    return true;
}

#include "command_response.inc"

static void on_motion_impl(void* u) {
    if (!custom || u!=unit) return;
    if (field(u,0x618)!=1 || field(u,0x977)!=cursor) {
        custom=false;
        int x=field(u,8),y=field(u,12),z=field(u,16);
        int c=field(u,0x977);
        if (field(u,0x618)==1 && c>=0 && c<field(u,0x97b)) {
            int* point=(int*)((char*)u+0x97f+c*28);
            x=point[0];y=point[1];z=point[2];
        }
        check_ownership(u,x,y,z);
        return;
    }
    int old_native_x=native_root_x/6,old_native_y=native_root_y/6;
    native_root_x+=field(u,0xb4f);native_root_y+=field(u,0xb53);
    progress+=field(u,0xb43)*scale;
    if (progress>=192) progress=192;
    if (progress<0) {custom=false;return;}
    field(u,0xb3f)=(int)progress;
    field(u,0xb47)=(int)((px-ax)*6+(tx-px)*6*progress/192);
    field(u,0xb4b)=(int)((py-ay)*6+(ty-py)*6*progress/192);
    field(u,0xb5b)=(int)(pz+(tz-pz)*progress/192)-field(u,0xb5f);
    if (animation_motion_trial) {
        // Native offsets cancel the animation's root motion. Cancel only
        // that motion, not the separately retargeted physical displacement.
        int next_x=ax+field(u,0xb47)/6,next_y=ay+field(u,0xb4b)/6;
        field(u,0xb7b)+=next_x-field(u,0x14)-(native_root_x/6-old_native_x);
        field(u,0xb7f)+=next_y-field(u,0x18)-(native_root_y/6-old_native_y);
    }
}

// A completed segment can be followed by a new route whose cursor starts at
// the same value. Cursor equality alone cannot identify the old interpolation.
static void on_finish_impl(void* u) {
    if (custom && u==unit) {
        log_event("finish_custom",u,cursor,(int)progress);
        custom=false;
    }
}
static void on_animation_restore_impl(void* u) {
    if (custom && u==unit) {
        log_event("animation_handoff",u,field(u,0xb7b),field(u,0xb7f));
    }
}

static void __cdecl on_order(void* u) {
    int index=state_index(u);if(index<0)return;
    load_state(u,index);if(!pursuit_to_move(u))on_order_impl(u);save_state(index);
}
static void __cdecl on_motion(void* u) {
    int index=state_index(u);if(index<0)return;
    load_state(u,index);
    if(loaded_route_pending[index]){loaded_route_pending[index]=false;on_order_impl(u,true);}
    on_motion_impl(u);save_state(index);
}
static void __cdecl on_finish(void* u) {
    int index=state_index(u);if(index<0)return;
    load_state(u,index);on_finish_impl(u);save_state(index);
}
static void __cdecl on_animation_restore(void* u) {
    int index=state_index(u);if(index<0)return;
    load_state(u,index);on_animation_restore_impl(u);save_state(index);
}


static void __cdecl on_draw(void* u,int x_base,int y,int x_extra,void* scene,int* stack) {
    int index=state_index(u);
    if(index>=0 && global(0x6e1f0c)<=1){
        const RedirectState& s=redirect_states[index];
        if(s.custom && s.identity==u && s.id==field(u,0) &&
           field(u,0x618)==1 && field(u,0x977)==s.cursor){
            // Native sort bounds cover A->D. A redirected P->D can extend
            // outside that edge even on flat ground. Include the occupied
            // physical cell without altering the screen position/collision.
            int rotation=field(scene,0x31)&3;
            int x=((field(u,0x14)+16)/32)*32+16;
            int y=((field(u,0x18)+16)/32)*32+16;
            int& sx=stack[0x18/4];int& sy=stack[0x14/4];
            sx=(rotation==0 || rotation==3)?max(sx,x):min(sx,x);
            sy=(rotation==0 || rotation==1)?max(sy,y):min(sy,y);
            stack[0x20/4]=max(stack[0x20/4],((field(u,0x1c)+15)/16)*16);
        }
    }
    if (logfile!=INVALID_HANDLE_VALUE && u==(void*)global(0x6def58)) {
        log_event("draw",u,x_base+x_extra,y);
        char line[256];DWORD n;LARGE_INTEGER q;QueryPerformanceCounter(&q);
        int len=_snprintf(line,sizeof(line),"%I64d,draw_state,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\r\n",
            q.QuadPart,field(u,8),field(u,12),field(u,16),field(u,0x14),field(u,0x18),
            field(u,0x608),field(u,0xb7b),field(u,0xb7f),field(u,0xb3f),
            field(u,0xb47),field(u,0xb4b),x_base,x_extra);
        if (logfile!=INVALID_HANDLE_VALUE && len>0) WriteFile(logfile,line,len,&n,0);
        len=_snprintf(line,sizeof(line),"%I64d,projection_state,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\r\n",
            q.QuadPart,field(scene,0x7d),field(scene,0x81),field(scene,0x85),
            field(scene,0x89),field(scene,0x8d),field(scene,0x31),
            stack[0x50/4],stack[0x54/4],stack[0x14/4],stack[0x18/4],
            field(u,0x608),field(u,0x610),field(u,0x618),
            field(u,0x5fc),field(u,0xb77),field(u,0xb8f));
        if (logfile!=INVALID_HANDLE_VALUE && len>0) WriteFile(logfile,line,len,&n,0);
        len=_snprintf(line,sizeof(line),"%I64d,height_state,%d,%d,%d,%d,%d,%d,%d,%d,%d\r\n",
            q.QuadPart,field(u,0x1c),field(u,0xb5b),field(u,0xb5f),field(u,0xb57),
            field(u,0xb83),field(u,0xb87),scene?field(scene,0x89):0,
            scene?field(scene,0x8d):0,scene?*(unsigned char*)((char*)scene+0x31):0);
        if (logfile!=INVALID_HANDLE_VALUE && len>0) WriteFile(logfile,line,len,&n,0);
    }
}
extern "C" BOOL __cdecl mm_redirect_prediction(void* u,double* x,double* y,double* h,double* limit){
    int index=state_index(u);if(index<0)return FALSE;
    const RedirectState& s=redirect_states[index];
    if(!s.custom || s.identity!=u || s.id!=field(u,0) ||
       field(u,0x618)!=1 || field(u,0x977)!=s.cursor)return FALSE;
    double step=field(u,0xb43)*s.scale;
    if(step<=0 || s.progress>=192)return FALSE;
    *x=(s.tx-s.px)*step/192;*y=(s.ty-s.py)*step/192;
    *h=(s.tz-s.pz)*step/192;*limit=(192-s.progress)/step;
    return TRUE;
}
// Capture the actual sprite-list position after the primary draw enqueue.
// The earlier 0x4fa261 hook only sees an intermediate cell-relative offset.
static void __cdecl on_sprite(void* u,void* queue,int site,void* scene) {
    if (logfile==INVALID_HANDLE_VALUE) return;
    if (u!=(void*)global(0x6def58)) return;
    char* next=*(char**)((char*)queue+4);
    int count=field(queue,8);
    if (!next || count<=0 || count>4096) return;
    char* entry=next-0x24;
    int* frame=*(int**)(entry+4);
    int world_x=field(u,0x14),world_y=field(u,0x18),height=field(u,0x1c);
    int camera_x=scene?field(scene,0x89):0,camera_y=scene?field(scene,0x8d):0;
    int camera_z=scene?field(scene,0x85):0;
    if (have_actor_queue) {
        int shift_x[512],shift_y[512],matches=0;
        for (int i=0;i<terrain_now_count;i++) for (int j=0;j<terrain_prev_count;j++) {
            if (terrain_now[i].key_a==terrain_prev[j].key_a &&
                terrain_now[i].key_b==terrain_prev[j].key_b) {
                shift_x[matches]=terrain_now[i].x-terrain_prev[j].x;
                shift_y[matches]=terrain_now[i].y-terrain_prev[j].y;
                matches++;break;
            }
        }
        int cam_dx=matches>=10?median_int(shift_x,matches):0;
        int cam_dy=matches>=10?median_int(shift_y,matches):0;
        int dx=world_x-actor_world_x,dy=world_y-actor_world_y;
        int expected_x=dx-dy+cam_dx+frame[3]-actor_frame_origin_x;
        int expected_y=(dx+dy)/2-height+actor_height+cam_dy+
                       frame[4]-actor_frame_origin_y;
        int error_x=*(int*)(entry+8)-last_actor_x-expected_x;
        int error_y=*(int*)(entry+12)-last_actor_y-expected_y;
        if (abs(error_x)>8 || abs(error_y)>8) {
            char diagnostic[192];DWORD written;LARGE_INTEGER q;QueryPerformanceCounter(&q);
            int length=_snprintf(diagnostic,sizeof(diagnostic),
                "%I64d,anchor_error,%d,%d,%d,%d,%d,%d,%d,%d\r\n",
                q.QuadPart,error_x,error_y,dx,dy,height-actor_height,
                camera_x-actor_camera_x,camera_y-actor_camera_y,custom?1:0);
            if (logfile!=INVALID_HANDLE_VALUE && length>0)
                WriteFile(logfile,diagnostic,length,&written,0);
        }
    }
    last_actor_x=*(int*)(entry+8);
    last_actor_y=*(int*)(entry+12);
    have_actor_queue=true;
    actor_world_x=world_x;actor_world_y=world_y;actor_height=height;
    actor_camera_x=camera_x;actor_camera_y=camera_y;actor_camera_z=camera_z;
    actor_frame_origin_x=frame[3];actor_frame_origin_y=frame[4];
    memcpy(terrain_prev,terrain_now,sizeof(TerrainSample)*terrain_now_count);
    terrain_prev_count=terrain_now_count;terrain_now_count=0;
    char line[256];DWORD n;LARGE_INTEGER q;QueryPerformanceCounter(&q);
    int len=_snprintf(line,sizeof(line),"%I64d,sprite%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\r\n",
        q.QuadPart,site,field(u,8),field(u,12),field(u,16),field(u,0x14),field(u,0x18),
        *(int*)entry,*(int*)(entry+4),*(int*)(entry+8),*(int*)(entry+12),
        *(int*)(entry+16),*(int*)(entry+20),*(int*)(entry+24),*(int*)(entry+28),
        frame[0],frame[1],frame[2],frame[3],frame[4],field(u,0xbf3));
    if (logfile!=INVALID_HANDLE_VALUE && len>0) WriteFile(logfile,line,len,&n,0);
}
static void __cdecl on_all_sprite(int* stack,void* queue) {
#ifdef MM_COMBINED
    mm_render_tag(stack,queue);
#endif
    if (logfile==INVALID_HANDLE_VALUE) return;
    unsigned site=(unsigned)stack[1];
    if (site<0x400000 || site>0x600000) return;
    void* u=(void*)global(0x6def58);
    char* next=*(char**)((char*)queue+4);
    int count=field(queue,8);
    if (!next || count<=0 || count>4096) return;
    char* entry=next-0x24;
    int ex=*(int*)(entry+8),ey=*(int*)(entry+12);
    if (site==0x4f8bf5 && terrain_now_count<512) {
        TerrainSample& sample=terrain_now[terrain_now_count++];
        sample.key_a=*(unsigned*)entry;sample.key_b=*(unsigned*)(entry+4);
        sample.x=ex;sample.y=ey;
    }
    if (site<0x4fa000 || site>0x4fbca9) {
        if (!have_actor_queue || abs(ex-last_actor_x)>140 || abs(ey-last_actor_y)>140) return;
    }
    char line[256];DWORD n;LARGE_INTEGER q;QueryPerformanceCounter(&q);
    int len=_snprintf(line,sizeof(line),"%I64d,sprite_any,%x,%x,%d,%d,%d,%d,%d,%d,%d,%d,%d\r\n",
        q.QuadPart,site,(unsigned)stack[0x20/4],field(u,8),field(u,12),field(u,16),field(u,0x14),field(u,0x18),
        *(int*)entry,*(int*)(entry+4),*(int*)(entry+8),*(int*)(entry+12));
    if (logfile!=INVALID_HANDLE_VALUE && len>0) WriteFile(logfile,line,len,&n,0);
}

static DWORD order_return=0x50fcf2, motion_return=0x5106e0,
             finish_return=0x512467,draw_return=0x4fa266,
             sprite_return=0x4fa62d,all_sprite_return=0x4fff46,
             animation_return=0x5108cf;
static DWORD request_return=0x5128a6;
static DWORD blocked_return=0x511be7,wait_return=0x50f829;
__declspec(naked) static void blocked_wait_hook() {
    __asm {
        mov dword ptr [esi+66ch],7
        pushfd
        pushad
        push esi
        call remember_blocked_wait
        add esp,4
        popad
        popfd
        jmp dword ptr [blocked_return]
    }
}
static DWORD dynamic_blocked_return=0x5112c3;
__declspec(naked) static void dynamic_blocked_wait_hook() {
    __asm {
        mov dword ptr [esi+66ch],5
        pushfd
        pushad
        push esi
        call remember_blocked_wait
        add esp,4
        popad
        popfd
        jmp dword ptr [dynamic_blocked_return]
    }
}
__declspec(naked) static void wait_tick_hook() {
    __asm {
        pushfd
        pushad
        push esi
        call wake_cleared_wait
        add esp,4
        popad
        popfd
        mov eax,[esi+66ch]
        jmp dword ptr [wait_return]
    }
}
// Extend only the ordinary ground-click allocator, after its original 17 slots.
// Native terrain/support/transition validation remains at 0x517b64 onward.
static int __cdecl extra_group_slot(void* u,int* stack) {
    if(global(0x6e1f0c)>1 || stack[5]!=0x4fefd0 || state_index(u)<0)return 0;
    void* type=*(void**)((char*)u+0xac);
    if(!type || field(type,8)!=1 || field(u,0x104)!=0 || field(type,0x44)!=1 ||
       *(unsigned char*)((char*)u+0x723) || field(u,0x5ec)==14)return 0;
    int slot=global(0x6e985c)-17,w=global(0x6c5494),h=global(0x6c5498);
    if(slot<0 || slot>=32 || w<9 || h<9)return 0;
    static const int offsets[32][2]={
        {0,-1},{-1,0},{1,0},{0,1},{-1,-2},{1,-2},{-2,-1},{2,-1},
        {-2,1},{2,1},{-1,2},{1,2},{0,-3},{-3,0},{3,0},{0,3},
        {-1,-3},{1,-3},{-3,-1},{3,-1},{-3,1},{3,1},{-1,3},{1,3},
        {-2,-3},{2,-3},{-3,-2},{3,-2},{-3,2},{3,2},{-2,3},{2,3}};
    int x=stack[6],y=stack[7];
    if(x<0 || x>=w || y<0 || y>=h)return 0;
    // Same toroidal coordinate convention as the native coordinate wrappers.
    *(int*)stack[10]=(x+offsets[slot][0]+w)%w;
    *(int*)stack[11]=(y+offsets[slot][1]+h)%h;
    return 1;
}
static DWORD group_original=0x517a8a,group_fallback=0x517d89,group_validate=0x517b64;
__declspec(naked) static void group_slot_hook() {
    __asm {
        cmp eax,10h
        jle original_slots
        pushfd
        pushad
        lea eax,[esp+24h]
        push eax
        push ebp
        call extra_group_slot
        add esp,8
        test eax,eax
        jz fallback_slot
        popad
        popfd
        mov eax,[esi]
        jmp dword ptr [group_validate]
    fallback_slot:
        popad
        popfd
        jmp dword ptr [group_fallback]
    original_slots:
        jmp dword ptr [group_original]
    }
}
static DWORD budget_return=0x513168;
__declspec(naked) static void budget_hook() {
    __asm {
        pushfd
        cmp dword ptr ds:[6e1f0ch],1
        jg native_request_budget
        // Match the already established direct/redirect search allowance.
        // Native early exit and the independent 16-waypoint output cap remain.
        mov dword ptr ds:[6df18ch],600
    native_request_budget:
        popfd
        mov esi,dword ptr ds:[6df188h]
        jmp dword ptr [budget_return]
    }
}
static DWORD reset_return=0x5060a7,deserialize_return=0x527316;
__declspec(naked) static void reset_hook() {
    __asm {
        pushfd
        pushad
        push ecx
        call on_unit_replaced
        add esp,4
        popad
        popfd
        push -1
        push 5c241bh
        jmp dword ptr [reset_return]
    }
}
__declspec(naked) static void deserialize_hook() {
    __asm {
        pushfd
        pushad
        push ecx
        call on_unit_replaced
        add esp,4
        push dword ptr [esp+18h]
        call mark_loaded_route
        add esp,4
        popad
        popfd
        sub esp,148h
        jmp dword ptr [deserialize_return]
    }
}
__declspec(naked) static void request_hook() {
    __asm {
        pushfd
        cmp dword ptr ds:[6e1f0ch],1
        jg native_budget
        // Single-player per-request limit is 600. A fresh 601 allowance
        // avoids cross-unit yielding, including the native fast-route path.
        mov dword ptr ds:[6df188h],601
    native_budget:
        popfd
        sub esp,2ach
        jmp dword ptr [request_return]
    }
}
__declspec(naked) static void order_hook() {
    __asm {
        pushfd
        pushad
        push esi
        call on_order
        add esp,4
        popad
        popfd
        mov ecx,[esi+6e8h]
        jmp dword ptr [order_return]
    }
}
__declspec(naked) static void motion_hook() {
    __asm {
        pushfd
        pushad
        push ebp
        call on_motion
        add esp,4
        popad
        popfd
        mov eax,[ebp+0b5bh]
        mov edx,[ebp+0b5fh]
        jmp dword ptr [motion_return]
    }
}
__declspec(naked) static void finish_hook() {
    __asm {
        pushfd
        pushad
        push ecx
        call on_finish
        add esp,4
        popad
        popfd
        sub esp,40h
        push ebx
        push ebp
        mov ebp,ecx
        jmp dword ptr [finish_return]
    }
}
__declspec(naked) static void draw_hook() {
    __asm {
        pushfd
        pushad
        mov eax,[esp]
        mov ecx,[esp+24]
        mov edx,[esp+20]
        mov ebx,[esp+8]
        lea edi,[esp+24h]
        push edi
        push esi
        push ebx
        push edx
        push ecx
        push eax
        call on_draw
        add esp,24
        popad
        popfd
        mov eax,[esi+31h]
        add ecx,ebp
        jmp dword ptr [draw_return]
    }
}
__declspec(naked) static void sprite_hook() {
    __asm {
        pushfd
        pushad
        mov eax,[esp+40h]
        push esi
        push 1
        push edi
        push eax
        call on_sprite
        add esp,16
        popad
        popfd
        mov ecx,[esp+1ch]
        mov [esp+80h],eax
        jmp dword ptr [sprite_return]
    }
}
__declspec(naked) static void all_sprite_hook() {
    __asm {
        pushfd
        pushad
        lea eax,[esp+24h]
        push ecx
        push eax
        call on_all_sprite
        add esp,8
        popad
        popfd
        mov eax,[ecx+8]
        pop esi
        dec eax
        jmp dword ptr [all_sprite_return]
    }
}
__declspec(naked) static void animation_hook() {
    __asm {
        pushfd
        pushad
        push ebp
        call on_animation_restore
        add esp,4
        popad
        popfd
        mov ecx,[ebp+0b83h]
        jmp dword ptr [animation_return]
    }
}
static bool patch(unsigned address,void* target,const unsigned char* expected,unsigned length) {
    if (memcmp((void*)address,expected,length)) return false;
    DWORD old; if (!VirtualProtect((void*)address,length,PAGE_EXECUTE_READWRITE,&old)) return false;
    if (length<5 || length>16) return false;
    unsigned char data[16];memset(data,0x90,sizeof(data));data[0]=0xe9;
    *(DWORD*)(data+1)=(DWORD)target-address-5;
    memcpy((void*)address,data,length);
    FlushInstructionCache(GetCurrentProcess(),(void*)address,length);
    DWORD unused;VirtualProtect((void*)address,length,old,&unused);return true;
}
BOOL WINAPI DllMain(HINSTANCE h,DWORD reason,LPVOID) {
    if (reason==DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(h);
#ifdef MM_ALL_IN_ONE
        if (!mm_clock_initialize(h)) return FALSE;
#endif
        char rollback_setting[4]={0};
        GetEnvironmentVariableA("MM_PROBE_FORCE_ROLLBACK",rollback_setting,sizeof(rollback_setting));
        force_rollback=rollback_setting[0]=='1' && rollback_setting[1]==0;
        char enable_setting[4]={0};
        GetEnvironmentVariableA("MM_PROBE_ENABLE_REDIRECT",enable_setting,sizeof(enable_setting));
        disable_redirect=!(enable_setting[0]=='1' && enable_setting[1]==0);
        char animation_setting[4]={0};
        GetEnvironmentVariableA("MM_PROBE_ANIMATION_MOTION",animation_setting,sizeof(animation_setting));
        animation_motion_trial=animation_setting[0]=='1' && animation_setting[1]==0;
        char layer_setting[4]={0};
        GetEnvironmentVariableA("MM_PROBE_LAYER_REDIRECT",layer_setting,sizeof(layer_setting));
        layer_redirect_trial=animation_motion_trial && layer_setting[0]=='1' && layer_setting[1]==0;
        const unsigned char a[]={0x8b,0x8e,0xe8,6,0,0},b[]={0x8b,0x95,0x5f,0xb,0,0};
        const unsigned char c[]={0x83,0xec,0x40,0x53,0x55,0x8b,0xe9};
        const unsigned char d[]={0x8b,0x46,0x31,0x03,0xcd};
        const unsigned char e[]={0x8b,0x4c,0x24,0x1c,0x89,0x84,0x24,0x80,0,0,0};
        const unsigned char g[]={0x8b,0x41,0x08,0x5e,0x48};
        const unsigned char anim_bytes[]={0x8b,0x8d,0x83,0x0b,0,0};
        const unsigned char request_bytes[]={0x81,0xec,0xac,0x02,0,0};
        const unsigned char budget_bytes[]={0x8b,0x35,0x88,0xf1,0x6d,0};
        const unsigned char group_bytes[]={0x83,0xf8,0x10,0x0f,0x8f,0xff,0x02,0,0};
        const unsigned char blocked_bytes[]={0xc7,0x86,0x6c,0x06,0,0,0x07,0,0,0};
        const unsigned char dynamic_blocked_bytes[]={0xc7,0x86,0x6c,0x06,0,0,0x05,0,0,0};
        const unsigned char wait_bytes[]={0x8b,0x86,0x6c,0x06,0,0};
        const unsigned char reset_bytes[]={0x6a,0xff,0x68,0x1b,0x24,0x5c,0};
        const unsigned char deserialize_bytes[]={0x81,0xec,0x48,0x01,0,0};
        if (memcmp((void*)0x50fcec,a,6) || memcmp((void*)0x5106da,b,6) ||
            memcmp((void*)0x512460,c,7) || memcmp((void*)0x4fa261,d,5) ||
            memcmp((void*)0x4fa622,e,11) || memcmp((void*)0x4fff41,g,5) ||
            memcmp((void*)0x5108c9,anim_bytes,6) ||
            memcmp((void*)0x5128a0,request_bytes,6) ||
            memcmp((void*)0x5060a0,reset_bytes,7) ||
            memcmp((void*)0x527310,deserialize_bytes,6) ||
            memcmp((void*)0x513162,budget_bytes,6) ||
            memcmp((void*)0x517a81,group_bytes,9) ||
            memcmp((void*)0x511bdd,blocked_bytes,10) ||
            memcmp((void*)0x5112b9,dynamic_blocked_bytes,10) ||
            memcmp((void*)0x50f823,wait_bytes,6)) return FALSE;
        char trace_setting[4]={0};
        GetEnvironmentVariableA("MM_PROBE_REPATH_TRACE",trace_setting,sizeof(trace_setting));
        if (trace_setting[0]=='1' && trace_setting[1]==0)
            logfile=CreateFileA("modernization\\logs\\repath-trial.csv",FILE_APPEND_DATA,
                FILE_SHARE_READ|FILE_SHARE_WRITE,0,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
        const unsigned char direct_bytes[]={0x8b,0x8c,0x24,0xc4,0x02,0,0};
        if (!patch(0x51292f,(void*)short_direct_hook,direct_bytes,7)) return FALSE;
        if (!patch(0x512460,(void*)finish_hook,c,7)) return FALSE;
        if (!patch(0x4fa261,(void*)draw_hook,d,5)) return FALSE;
        if (!patch(0x4fa622,(void*)sprite_hook,e,11)) return FALSE;
        if (!patch(0x4fff41,(void*)all_sprite_hook,g,5)) return FALSE;
        if (!patch(0x5108c9,(void*)animation_hook,anim_bytes,6)) return FALSE;
        if (!patch(0x5106da,(void*)motion_hook,b,6)) return FALSE;
        if (!patch(0x50fcec,(void*)order_hook,a,6)) return FALSE;
        const unsigned char attack_bytes[]={0xe8,0x39,0xfb,0xff,0xff};
        if (!patch(0x50aef2,(void*)attack_response_hook,attack_bytes,5)) return FALSE;
        if (!patch(0x5128a0,(void*)request_hook,request_bytes,6)) return FALSE;
        if (!patch(0x5060a0,(void*)reset_hook,reset_bytes,7)) return FALSE;
        if (!patch(0x527310,(void*)deserialize_hook,deserialize_bytes,6)) return FALSE;
        if (!patch(0x513162,(void*)budget_hook,budget_bytes,6)) return FALSE;
        if (!patch(0x517a81,(void*)group_slot_hook,group_bytes,9)) return FALSE;
        if (!patch(0x511bdd,(void*)blocked_wait_hook,blocked_bytes,10)) return FALSE;
        if (!patch(0x5112b9,(void*)dynamic_blocked_wait_hook,dynamic_blocked_bytes,10)) return FALSE;
        if (!patch(0x50f823,(void*)wait_tick_hook,wait_bytes,6)) return FALSE;
#ifdef MM_COMBINED
        if (!mm_render_initialize()) return FALSE;
#endif
#ifdef MM_ALL_IN_ONE
        if (!mm_logic_time_initialize(h) || !mm_game_time_initialize(h)) return FALSE;
#endif
    }
    return TRUE;
}
