// Owned-harness experiment: copy native drawing commands, never rerun simulation.
#include <windows.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

static int& f(void* p,unsigned o) {return *(int*)((char*)p+o);}
static int g(unsigned a) {return *(int*)a;}
struct Command { unsigned char bytes[36]; };
struct Actor {void* pointer; int x,y,h,dx,dy,dh,rise; double phase,speed,step_x,step_y,step_h,frac_x,frac_y,max_phase;};
struct Tag {Command command;void* actor;};
static Command saved[12000],scratch[12000],native_commands[12000];
static Tag tags[5000];static int tags_count;
static Actor actors[4096],previous[4096];
static int owners[12000],command_count,bar_count;
static int tagged_commands,moving_actors;
static int predicted_commands;
static int delta_commands;
struct Bar {void* object;int actor;int x,y;};
static Bar bars[60];
// The frozen renderer is 800x600 only. This candidate also supports the HD
// engine's verified 1120x840 surface; storage is bounded by that maximum.
static const int kMaxWidth=1120,kMaxHeight=840,kBytesPerPixel=2;
static unsigned char background[kMaxWidth*kMaxHeight*kBytesPerPixel];
static unsigned char complete[kMaxWidth*kMaxHeight*kBytesPerPixel];
static unsigned char final_surface[kMaxWidth*kMaxHeight*kBytesPerPixel];
static int clip[4],pitch,frame_width,frame_height,frame_row_bytes;
static bool ready,busy,replay_enabled;
static bool captured,render_log_enabled,light_log,armed;static int rotation;
static int prior_skip_max;
static bool continuous_enabled,native_bars_shifted;
static LARGE_INTEGER frequency,frame_qpc,previous_qpc;
static DWORD render_thread,last_frame_tick;
static HANDLE logfile=INVALID_HANDLE_VALUE;
static DWORD before_resume=0x4fd559,finish_resume=0x4fd5ad,tag_resume=0x4fff46;
static DWORD draw_address=0x5002a0;
static DWORD (WINAPI* original_tick)();
typedef void* (__thiscall* LockFn)(void*);
typedef void (__thiscall* DrawFn)(void*);
typedef void (__thiscall* ImageFn)(void*,void*,void*);
typedef void (__thiscall* PresentFn)(void*,void*,int,int);
static void draw_context(unsigned char* buffer,int stride,const int* rectangle) {
    __asm {
        mov ecx,buffer
        mov edx,stride
        shr edx,1
        mov eax,frame_height
        push eax
        mov eax,57dc20h
        call eax
        mov eax,rectangle
        push dword ptr [eax+12]
        push dword ptr [eax+8]
        mov ecx,[eax+4]
        mov edx,[eax]
        mov eax,57dc60h
        call eax
    }
}

static unsigned hash_frame(unsigned char* p) {
    unsigned h=2166136261u;
    for (int y=0;y<frame_height;y++)for(int x=0;x<frame_row_bytes;x++)
        h=(h^p[y*pitch+x])*16777619u;
    return h;
}
static unsigned hash_ui(unsigned char* p){
    unsigned h=2166136261u;
    for(int y=0;y<frame_height;y++)for(int x=0;x<frame_width;x++){
        if(x>=clip[0] && x<clip[2] && y>=clip[1] && y<clip[3])continue;
        h=(h^*(uint16_t*)(p+y*pitch+x*2))*16777619u;
    }
    return h;
}
static void log_frame(const char* kind,unsigned char* p,int moved) {
    if(!render_log_enabled && !light_log)return;
    LARGE_INTEGER q;QueryPerformanceCounter(&q);char line[160];DWORD written;
    unsigned checksum=render_log_enabled?hash_frame(p):0;
    int n=_snprintf(line,sizeof(line),"%I64d,%s,%d,%d,%08X,%d,%d,%d,%d,%d,%d,%d\r\n",q.QuadPart,kind,
        g(0x6c4830),command_count,checksum,moved,bar_count,pitch,tagged_commands,moving_actors,predicted_commands,delta_commands);
    if(logfile!=INVALID_HANDLE_VALUE && n>0)WriteFile(logfile,line,n,&written,0);
}
static int actor_index(void* actor) {
    uintptr_t base=(uintptr_t)g(0x6def58),pointer=(uintptr_t)actor;
    int count=g(0x6def5c);
    if(count<=0 || count>4096 || pointer<base || pointer>=base+(uintptr_t)count*0xe4b ||
       (pointer-base)%0xe4b) return -1;
    return (int)((pointer-base)/0xe4b);
}
static void __cdecl tag_command(int* stack,void* queue) {
    unsigned site=(unsigned)stack[1];
    if(site<0x4fa000 || site>0x4fbca9 || tags_count>=5000 || f(queue,8)<=0)return;
    void* actor=(void*)stack[0x5c/4];
    if(actor_index(actor)<0)return;
    tags[tags_count].actor=actor;
    memcpy(&tags[tags_count++].command,(char*)f(queue,4)-36,36);
}
#ifdef MM_COMBINED
extern "C" void __cdecl mm_render_tag(int* stack,void* queue){tag_command(stack,queue);}
#endif
static void restore_frame_skip(){
    if(armed){
        if(prior_skip_max==1 && g(0x5e1418)==0)*(int*)0x5e1418=1;
        armed=false;
    }
}
static void __cdecl before_draw(void* scene,void* queue,unsigned char* buffer) {
    ready=false;captured=false;command_count=0;
    int count=f(queue,8);
    int candidate_pitch=f((void*)0x6a49e0,0x18);
    int candidate_width=g(0x6a49f0),candidate_height=g(0x6a49f4);
    bool known_surface=(candidate_width==800 && candidate_height==600) ||
                       (candidate_width==1120 && candidate_height==840);
    bool eligible=replay_enabled && g(0x6de6fd)==30 && g(0x6e1f0c)<=1 &&
                  known_surface &&
                  g(0x6e1f68)==0 && buffer && count>0 && count<=12000 &&
                  candidate_pitch>=candidate_width*kBytesPerPixel &&
                  candidate_pitch<=16384;
    if(!eligible){
        restore_frame_skip();
        tags_count=0;return;
    }
    if(!armed){
        int current_skip=g(0x5e1418);
        if(current_skip<0 || current_skip>1){tags_count=0;return;}
        prior_skip_max=current_skip;
        *(int*)0x5e1418=0;armed=true;
    }
    pitch=candidate_pitch;frame_width=candidate_width;frame_height=candidate_height;
    frame_row_bytes=frame_width*kBytesPerPixel;
    render_thread=GetCurrentThreadId();command_count=count;
    rotation=*(unsigned char*)((char*)scene+0x31);
    memcpy(saved,(void*)f(queue,0),count*36);
    for(int y=0;y<frame_height;y++)
        memcpy(background+y*frame_row_bytes,buffer+y*pitch,frame_row_bytes);
    memcpy(clip,(void*)g(0x6c482c),sizeof(clip));
    if(clip[0]<0 || clip[1]<0 || clip[2]>frame_width || clip[3]>frame_height ||
       clip[0]>=clip[2] || clip[1]>=clip[3]){
        restore_frame_skip();tags_count=0;return;
    }
    if(render_log_enabled || light_log){
        char line[128];DWORD written;LARGE_INTEGER q;QueryPerformanceCounter(&q);
        int n=_snprintf(line,sizeof(line),"%I64d,viewport,%d,%d,%d,%d\r\n",
                       q.QuadPart,clip[0],clip[1],clip[2],clip[3]);
        if(logfile!=INVALID_HANDLE_VALUE && n>0)WriteFile(logfile,line,n,&written,0);
    }
    memcpy(previous,actors,sizeof(actors));
    int unit_count=g(0x6def5c);
    if(unit_count<=0 || unit_count>4096){tags_count=0;return;}
    moving_actors=0;
    for(int i=0;i<unit_count;i++){
        void* unit=(char*)g(0x6def58)+i*0xe4b;
        Actor& a=actors[i];Actor& old=previous[i];
        a.pointer=unit;a.x=f(unit,0x14);a.y=f(unit,0x18);a.h=f(unit,0x1c);
        a.dx=a.x-old.x;a.dy=a.y-old.y;a.dh=a.h-old.h;
        if(old.pointer!=unit || abs(a.dx)>16 || abs(a.dy)>16 || abs(a.dh)>16 ||
           !f(unit,4) || f(unit,0x618)!=1){a.dx=a.dy=a.dh=0;}
        if(a.dx || a.dy || a.dh)moving_actors++;
        a.phase=a.speed=a.step_x=a.step_y=a.step_h=a.frac_x=a.frac_y=0;a.max_phase=0;
        a.rise=f(unit,0xb5b);
        int threshold=f(unit,0xb67),remainder=f(unit,0xb6b);
        if(f(unit,0x618)==1 && f(unit,0x10c)==0 &&
           threshold>0 && remainder>=0 && remainder<threshold && f(unit,0xb3f)<192){
            a.phase=(double)remainder/threshold;
            a.speed=(double)f(unit,0xb63)/threshold;
            a.step_x=f(unit,0xb4f)/6.0;a.step_y=f(unit,0xb53)/6.0;
            a.step_h=(double)f(unit,0xb57)*f(unit,0xb43)/192;
            a.frac_x=(f(unit,0xb47)%6)/6.0;a.frac_y=(f(unit,0xb4b)%6)/6.0;
            a.max_phase=f(unit,0xb43)>0?(192.0-f(unit,0xb3f))/f(unit,0xb43):0;
            if(a.max_phase>2)a.max_phase=2;
        }
        if(i==0 && render_log_enabled){
            char line[256];DWORD n;LARGE_INTEGER q;QueryPerformanceCounter(&q);
            int len=_snprintf(line,sizeof(line),"%I64d,phase,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\r\n",
                q.QuadPart,a.x,a.y,a.h,f(unit,0x618),threshold,remainder,f(unit,0xb63),
                f(unit,0xb4f),f(unit,0xb53),f(unit,0xb43),f(unit,0xb57),f(unit,0xb3f));
            if(logfile!=INVALID_HANDLE_VALUE && len>0)WriteFile(logfile,line,len,&n,0);
        }
    }
    tagged_commands=0;
    for(int i=0;i<count;i++){
        owners[i]=-1;
        for(int j=0;j<tags_count;j++)if(!memcmp(&saved[i],&tags[j].command,36)){
            owners[i]=actor_index(tags[j].actor);break;
        }
        if(owners[i]>=0)tagged_commands++;
    }
    tags_count=0;bar_count=f(scene,0x1e5);
    if(bar_count<0 || bar_count>60)bar_count=0;
    for(int i=0;i<bar_count;i++){
        void* object=*(void**)((char*)scene+0xf5+i*4);
        bars[i].object=object;bars[i].actor=actor_index((char*)object-0x6b4);
        bars[i].x=f(object,8);bars[i].y=f(object,12);
    }
    previous_qpc=frame_qpc;QueryPerformanceCounter(&frame_qpc);
    last_frame_tick=original_tick();
    captured=true;
}
static void projected_shift_exact(const Actor& a,double elapsed_ticks,double* x,double* y) {
    double wx,wy,h;
    if(continuous_enabled){
        double phase=a.phase+a.speed*elapsed_ticks;
        // Stay inside the current native route edge. Height saturation must
        // not freeze XY movement: native motion clamps those independently.
        if(phase>a.max_phase)phase=a.max_phase;
        wx=a.frac_x+a.step_x*phase;wy=a.frac_y+a.step_y*phase;h=a.step_h*phase;
        if(a.rise+h>16)h=16-a.rise;
        if(a.rise+h<-16)h=-16-a.rise;
    }else{wx=a.dx*elapsed_ticks;wy=a.dy*elapsed_ticks;h=a.dh*elapsed_ticks;}
    double sx=0,sy=0;
    switch(rotation&3){
        case 0:sx=wx-wy;sy=(wx+wy)*0.5;break;
        case 1:sx=wx+wy;sy=(wy-wx)*0.5;break;
        case 2:sx=wy-wx;sy=-(wx+wy)*0.5;break;
        case 3:sx=-wx-wy;sy=(wx-wy)*0.5;break;
    }
    *x=sx;*y=sy-h;
}
static void projected_shift(const Actor& a,double elapsed_ticks,int* x,int* y) {
    double sx,sy;projected_shift_exact(a,elapsed_ticks,&sx,&sy);
    *x=(int)floor(sx+0.5);*y=(int)floor(sy+0.5);
}
static int shifted_commands(double fraction,int override_actor,int override_x,int override_y) {
    memcpy(scratch,saved,command_count*36);int moved=0;
    predicted_commands=0;
    delta_commands=0;
    for(int i=0;i<command_count;i++)if(owners[i]>=0){
        int dx,dy;projected_shift(actors[owners[i]],fraction,&dx,&dy);
        if(owners[i]==override_actor){dx=override_x;dy=override_y;}
        if(dx || dy)predicted_commands++;
        *(int*)(scratch[i].bytes+8)+=dx;*(int*)(scratch[i].bytes+12)+=dy;
        if(dx || dy)moved++;
        if(fraction>0 && (memcmp(&scratch[i],&native_commands[i],36)))delta_commands++;
    }
    return moved;
}
static void shift_bars(double fraction) {
    for(int i=0;i<bar_count;i++){
        Bar& b=bars[i];int dx=0,dy=0;
        if(b.actor>=0)projected_shift(actors[b.actor],fraction,&dx,&dy);
        f(b.object,8)=b.x+dx;f(b.object,12)=b.y+dy;
    }
}
static void restore_bars(){
    for(int i=0;i<bar_count;i++){f(bars[i].object,8)=bars[i].x;f(bars[i].object,12)=bars[i].y;}
}
static void __cdecl capture_and_draw(void* scene,void* queue,unsigned char* buffer){
    before_draw(scene,queue,buffer);
    native_bars_shifted=false;
    if(captured && continuous_enabled){
        shifted_commands(0,-1,0,0);
        memcpy(native_commands,scratch,command_count*36);
        int private_queue[6]={(int)scratch,(int)(scratch+command_count),command_count,12000,0,0};
        ((DrawFn)0x5002a0)(private_queue);
        shift_bars(0);native_bars_shifted=true;
    }else ((DrawFn)0x5002a0)(queue);
}
static void __cdecl finish_draw(unsigned char* buffer) {
    if(native_bars_shifted){restore_bars();native_bars_shifted=false;}
    if(!captured || !command_count || !buffer)return;
    for(int y=0;y<frame_height;y++)
        memcpy(complete+y*frame_row_bytes,buffer+y*pitch,frame_row_bytes);
    ready=true;log_frame("native",buffer,0);
}
static int draw_replay_variant(unsigned char* buffer,double fraction,
                               int override_actor,int override_x,int override_y){
    draw_context(buffer,pitch,clip);
    // Native UI is composed after the scene. Preserve pixels outside the
    // captured scene viewport instead of clearing the entire game surface.
    for(int y=clip[1];y<clip[3];y++)
        memcpy(buffer+y*pitch+clip[0]*2,background+y*frame_row_bytes+clip[0]*2,
               (clip[2]-clip[0])*2);
    int moved=shifted_commands(fraction,override_actor,override_x,override_y);
    int queue[6]={(int)scratch,(int)(scratch+command_count),command_count,12000,0,0};
    ((DrawFn)0x5002a0)(queue);
    draw_context(buffer,pitch,clip);
    for(int i=0;i<bar_count;i++){
        Bar& b=bars[i];int dx=0,dy=0;
        if(b.actor>=0)projected_shift(actors[b.actor],fraction,&dx,&dy);
        if(b.actor==override_actor){dx=override_x;dy=override_y;}
        int oldx=f(b.object,8),oldy=f(b.object,12);
        f(b.object,8)=b.x+dx;f(b.object,12)=b.y+dy;
        ((ImageFn)0x58f9c0)(b.object,buffer,(void*)0x6a49e0);
        f(b.object,8)=oldx;f(b.object,12)=oldy;
    }
    return moved;
}
static void replay() {
    if(!ready || busy || !replay_enabled || GetCurrentThreadId()!=render_thread)return;
    LARGE_INTEGER now;QueryPerformanceCounter(&now);
    double elapsed=(double)(now.QuadPart-frame_qpc.QuadPart)/frequency.QuadPart;
    if(elapsed<0.015 || elapsed>0.032 || last_frame_tick==0)return;
    double span=(double)(frame_qpc.QuadPart-previous_qpc.QuadPart)/frequency.QuadPart;
    if(span<=0 || span>0.15)return;
    busy=true;last_frame_tick=0;
    unsigned char* buffer=(unsigned char*)((LockFn)0x58b660)((void*)0x6a49e0);
    if(!buffer){busy=false;return;}
    for(int y=0;y<frame_height;y++)
        memcpy(final_surface+y*frame_row_bytes,buffer+y*pitch,frame_row_bytes);
    unsigned ui_before=(render_log_enabled || light_log)?hash_ui(buffer):0;
    int saved_clip[4];memcpy(saved_clip,(void*)g(0x6c482c),16);
    memcpy((void*)g(0x6c482c),clip,16);
    // Keep all seven global compositor parameters scoped to this draw.
    const unsigned context_addresses[]={0x658174,0x6a2dc8,0x6def50,0x6cbb6c,0x6e0008,0x6a49b8,0x656618};
    int old_context[7];for(int i=0;i<7;i++)old_context[i]=g(context_addresses[i]);
    double fraction=elapsed/span;if(fraction>0.75)fraction=0.75;
    int counters[3]={g(0x6e8db0),g(0x6e8db4),g(0x6e8db8)};
    *(int*)0x6e8db0=*(int*)0x6e8db4=*(int*)0x6e8db8=0;
    int moved=draw_replay_variant(buffer,fraction,-1,0,0);
    // Preserve pixels composed after the native scene (HUD, panels, cursor).
    // Those draws are not represented in the captured scene command queue.
    int overlay_pixels=0;
    for(int y=0;y<frame_height;y++){
        uint16_t* scene=(uint16_t*)(complete+y*frame_row_bytes);
        uint16_t* final=(uint16_t*)(final_surface+y*frame_row_bytes);
        uint16_t* target=(uint16_t*)(buffer+y*pitch);
        for(int x=0;x<frame_width;x++)if(scene[x]!=final[x]){
            target[x]=final[x];overlay_pixels++;
        }
    }
    *(int*)0x6e8db0=counters[0];*(int*)0x6e8db4=counters[1];*(int*)0x6e8db8=counters[2];
    memcpy((void*)g(0x6c482c),saved_clip,16);
    for(int i=0;i<7;i++)*(int*)context_addresses[i]=old_context[i];
    if(render_log_enabled || light_log){
        unsigned ui_after=hash_ui(buffer);char line[128];DWORD written;
        int n=_snprintf(line,sizeof(line),"%I64d,ui_preserved,%08X,%08X,%d,%d\r\n",
                       now.QuadPart,ui_before,ui_after,ui_before==ui_after,overlay_pixels);
        if(logfile!=INVALID_HANDLE_VALUE && n>0)WriteFile(logfile,line,n,&written,0);
    }
    log_frame("replay",buffer,moved);
    void* surface=(void*)g(0x6a49e4);
    typedef HRESULT (__stdcall* UnlockFn)(void*,void*);
    ((UnlockFn)(*(void***)surface)[0x80/4])(surface,buffer);
    ((PresentFn)0x58bf40)((void*)0x6a49e0,(void*)0x6a4fe0,0,0);
    busy=false;
}
static DWORD WINAPI clock_hook(){
    DWORD value=original_tick();
    if(armed && GetCurrentThreadId()==render_thread &&
       (g(0x6de6fd)!=30 || g(0x6e1f0c)>1 ||
                 g(0x6a49f0)!=frame_width || g(0x6a49f4)!=frame_height ||
                 g(0x6e1f68)!=0)){
        ready=false;restore_frame_skip();
    }
    replay();return value;
}
__declspec(naked) static void before_hook(){__asm{
    pushfd
    pushad
    push ebx
    push ebp
    push esi
    call capture_and_draw
    add esp,12
    popad
    popfd
    jmp dword ptr [before_resume]
}}
__declspec(naked) static void finish_hook(){__asm{
    pushfd
    pushad
    push ebx
    call finish_draw
    add esp,4
    popad
    popfd
    push eax
    call dword ptr [ecx+80h]
    jmp dword ptr [finish_resume]
}}
__declspec(naked) static void tag_hook(){__asm{
    pushfd
    pushad
    lea eax,[esp+24h]
    push ecx
    push eax
    call tag_command
    add esp,8
    popad
    popfd
    mov eax,[ecx+8]
    pop esi
    dec eax
    jmp dword ptr [tag_resume]
}}
static bool patch(unsigned address,void* target,const unsigned char* expected,unsigned n){
    if(memcmp((void*)address,expected,n))return false;DWORD old;
    if(!VirtualProtect((void*)address,n,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char bytes[8]={0xe9,0,0,0,0,0x90,0x90,0x90};*(DWORD*)(bytes+1)=(DWORD)target-address-5;
    memcpy((void*)address,bytes,n);FlushInstructionCache(GetCurrentProcess(),(void*)address,n);
    DWORD unused;VirtualProtect((void*)address,n,old,&unused);return true;
}
static BOOL initialize_render(){
        QueryPerformanceFrequency(&frequency);
        const unsigned char before[]={0x8b,0xcd,0xe8,0x47,0x2d,0,0};
        const unsigned char finish[]={0x50,0xff,0x91,0x80,0,0,0};
        const unsigned char tag[]={0x8b,0x41,0x08,0x5e,0x48};
        if(memcmp((void*)0x4fd552,before,7) || memcmp((void*)0x4fd5a6,finish,7)
#ifndef MM_COMBINED
           || memcmp((void*)0x4fff41,tag,5)
#endif
           )return FALSE;
        logfile=CreateFileA("modernization\\logs\\render-replay.csv",FILE_APPEND_DATA,
            FILE_SHARE_READ|FILE_SHARE_WRITE,0,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
        char setting[4]={0};GetEnvironmentVariableA("MM_PROBE_RENDER_REPLAY",setting,sizeof(setting));
        replay_enabled=setting[0]=='1' && !setting[1];
        GetEnvironmentVariableA("MM_PROBE_RENDER_CONTINUOUS",setting,sizeof(setting));
        continuous_enabled=setting[0]=='1' && !setting[1];
        GetEnvironmentVariableA("MM_PROBE_RENDER_LOG",setting,sizeof(setting));
        render_log_enabled=setting[0]=='1' && !setting[1];
        GetEnvironmentVariableA("MM_PROBE_RENDER_LIGHT_LOG",setting,sizeof(setting));
        light_log=setting[0]=='1' && !setting[1];
        original_tick=(DWORD(WINAPI*)())g(0x5c5164);
        if(!patch(0x4fd552,(void*)before_hook,before,7) ||
           !patch(0x4fd5a6,(void*)finish_hook,finish,7))return FALSE;
#ifndef MM_COMBINED
        if(!patch(0x4fff41,(void*)tag_hook,tag,5))return FALSE;
#endif
        DWORD old;if(!VirtualProtect((void*)0x5c5164,4,PAGE_READWRITE,&old))return FALSE;
        *(void**)0x5c5164=(void*)clock_hook;DWORD unused;VirtualProtect((void*)0x5c5164,4,old,&unused);
    return TRUE;
}
#ifdef MM_COMBINED
extern "C" BOOL __cdecl mm_render_initialize(){return initialize_render();}
#else
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID){
    if(reason==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(instance);return initialize_render();}
    return TRUE;
}
#endif
