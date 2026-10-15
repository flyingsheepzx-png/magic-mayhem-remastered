#pragma once
/* One mode policy for 1.1 fonts, composition, replay eligibility and input.
 * The engine primary is 2560x1440; independent UI content is native 1920x1440.
 * Battle pixels/controls remain native 1280x720, presented at exactly 2x. */
#include <windows.h>
#include <stdint.h>
#include <string.h>
#ifndef MM_HD_CONTROL_COUNT
#define MM_HD_CONTROL_COUNT 0x642c68
#define MM_HD_CONTROL_TABLE 0x642034
#endif
#define MM_HD_UI 2
#define MM_HD_BATTLE 1
typedef struct MmHdLayoutContext {
    int mode, content_x, content_y, content_width, content_height;
    int output_width, output_height, output_scale, font_scale;
} MmHdLayoutContext;
static __inline MmHdLayoutContext mm_hd_profile(int battle) {
    MmHdLayoutContext c;
    c.mode=battle?MM_HD_BATTLE:MM_HD_UI;
    c.content_x=battle?0:320;c.content_y=0;
    c.content_width=battle?1280:1920;c.content_height=battle?720:1440;
    c.output_width=2560;c.output_height=1440;
    c.output_scale=battle?2:1;c.font_scale=battle?1:2;
    return c;
}
static __inline POINT mm_hd_input(MmHdLayoutContext c,int x,int y) {
    POINT p={x/c.output_scale,y/c.output_scale};return p;
}
static __inline BOOL mm_hd_readable(const void* pointer,SIZE_T bytes) {
    MEMORY_BASIC_INFORMATION m;SIZE_T a=(SIZE_T)pointer,end=a+bytes;
    if(!pointer || end<a || !VirtualQuery(pointer,&m,sizeof(m)) ||
       m.State!=MEM_COMMIT || (m.Protect&(PAGE_NOACCESS|PAGE_GUARD)))return FALSE;
    return end<=(SIZE_T)m.BaseAddress+m.RegionSize;
}
static __inline BOOL mm_hd_battle_controls(void) {
    int count=*(volatile int*)MM_HD_CONTROL_COUNT,i,a=0,b=0;
    if(count<=0 || count>400)return FALSE;
    for(i=0;i<count;i++) {
        const unsigned char* control=((const unsigned char**)MM_HD_CONTROL_TABLE)[i];
        DWORD vtable;int rect[4];
        if(!mm_hd_readable(control,0x21))return FALSE;
        vtable=*(const DWORD*)control;
        if(vtable==0x5c6ee8)a=1;if(vtable==0x5c6f54)b=1;
        if(vtable==0x5c6a8c)continue;
        /* Packed controls do not align their rectangle to a DWORD boundary. */
        memcpy(rect,control+0x11,sizeof(rect));
        if(rect[2]>1280 || rect[3]>720)return FALSE;
    }
    return a && b;
}
static __inline MmHdLayoutContext mm_hd_current(void) {
    return mm_hd_profile(mm_hd_battle_controls());
}
