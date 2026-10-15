#include "layout_context.h"
#ifndef MM_MIXED_H
#define MM_MIXED_H

/* Diagnostic compositor for the verified native-UI probe. The game owns the
 * 2560x1440 primary and paints battle only in its upper-left 1280x720 rect.
 * Keep that primary untouched: the next engine draw must see its own pixels.
 */
#include <windows.h>
#include "ddsurface.h"

BOOL mm_mixed_enabled(void);
IDirectDrawSurfaceImpl* mm_mixed_present(IDirectDrawSurfaceImpl* primary);
POINT mm_mixed_input_point(IDirectDrawSurfaceImpl* primary, int x, int y);
extern LONG mm_mixed_d3d9_uploads;
BOOL mm_mixed_redraw_begin(IDirectDrawSurfaceImpl* primary);
void mm_mixed_redraw_end(IDirectDrawSurfaceImpl* primary,int mode);

#ifdef MM_MIXED_IMPLEMENTATION
#include <string.h>
#include "dd.h"

#include "mm_engine_identity.h"

#include "presentation_epoch.h"
static MmPresentationEpoch mm_epoch;
static int mm_redraw_mode;
static unsigned char* mm_last_pixels;
static SIZE_T mm_last_capacity;
static IDirectDrawSurfaceImpl mm_last_surface;
static int mm_battle_art_ready(IDirectDrawSurfaceImpl* p);
static unsigned mm_control_signature(void){
    unsigned h=2166136261u;int i,count=*(int*)MM_HD_CONTROL_COUNT;
    if(count<0 || count>400)return 0;
    h=(h^(unsigned)count)*16777619u;
    for(i=0;i<count;++i){
        const unsigned char* p=((const unsigned char**)MM_HD_CONTROL_TABLE)[i];
        unsigned v;int rect[4],j;
        if(!mm_hd_readable(p,0x21))return 0;
        v=*(unsigned*)p;memcpy(rect,p+0x11,sizeof rect);
        h=(h^(unsigned)(SIZE_T)p)*16777619u;h=(h^v)*16777619u;
        for(j=0;j<4;++j)h=(h^(unsigned)rect[j])*16777619u;
    }
    return h;
}
BOOL mm_mixed_redraw_begin(IDirectDrawSurfaceImpl* p) {
    return mm_mixed_enabled() && p && (p->caps&DDSCAPS_PRIMARYSURFACE) &&
        p->width==2560 && p->height==1440 && p->bpp==16;
}
void mm_mixed_redraw_end(IDirectDrawSurfaceImpl* p,int mode) {
    (void)p;
    if(mode==MM_HD_BATTLE && mm_epoch.ready && mm_epoch.mode==MM_HD_UI &&
       !mm_battle_art_ready(p))return;
    if(mm_epoch_redraw(&mm_epoch,mode,mm_control_signature(),GetTickCount()))mm_redraw_mode=mode;
}
static IDirectDrawSurfaceImpl* mm_remember(IDirectDrawSurfaceImpl* p) {
    SIZE_T n=(SIZE_T)p->pitch*p->height;
    if(mm_last_capacity<n){
        unsigned char* q=(unsigned char*)HeapAlloc(GetProcessHeap(),0,n);
        if(!q)return p;
        if(mm_last_pixels)HeapFree(GetProcessHeap(),0,mm_last_pixels);
        mm_last_pixels=q;mm_last_capacity=n;
    }
    memcpy(mm_last_pixels,p->surface,n);mm_last_surface=*p;
    mm_last_surface.surface=mm_last_pixels;return p;
}
static unsigned char* mm_mixed_pixels;
static SIZE_T mm_mixed_capacity;
static IDirectDrawSurfaceImpl mm_mixed_surface;
LONG mm_mixed_d3d9_uploads;

static int mm_mixed_sharpen_level(void)
{
    char value[4] = { 0 };
    GetEnvironmentVariableA("MM_PROBE_BATTLE_SHARPEN", value, sizeof(value));
    return (value[0] == '1' || value[0] == '2') && value[1] == 0 ? value[0] - '0' : 0;
}

static int mm_mixed_clamp(int value, int maximum)
{
    return value < 0 ? 0 : (value > maximum ? maximum : value);
}

/* A nearest-neighbour 2x block has three same-colour neighbours per pixel.
 * Only the horizontal and vertical neighbour outside the block differ.
 * Calculate the exact post-scale five-tap result from the 1280x720 source. */
static unsigned short mm_mixed_sharpen_pixel(unsigned short c,
                                             unsigned short horizontal,
                                             unsigned short vertical, int shift)
{
    int red = (c >> 11) & 31, green = (c >> 5) & 63, blue = c & 31;
    red = mm_mixed_clamp(red + ((2 * red - ((horizontal >> 11) & 31) - ((vertical >> 11) & 31)) >> shift), 31);
    green = mm_mixed_clamp(green + ((2 * green - ((horizontal >> 5) & 63) - ((vertical >> 5) & 63)) >> shift), 63);
    blue = mm_mixed_clamp(blue + ((2 * blue - (horizontal & 31) - (vertical & 31)) >> shift), 31);
    return (unsigned short)((red << 11) | (green << 5) | blue);
}

BOOL mm_mixed_enabled(void)
{
    static LONG state;
    LONG value=InterlockedExchangeAdd(&state,0);
    if(!value){
        char flag[4]={0};
        GetEnvironmentVariableA("MM_PROBE_MIXED_RENDER",flag,sizeof(flag));
        value=flag[0]=='1' && flag[1]==0 && mm_hd11_current_engine()?2:1;
        InterlockedExchange(&state,value);
    }
    return value==2;
}

/* The engine keeps pixels from the preceding full-size page outside the
 * 1280x720 battle rectangle. Classify by live controls, not stale pixels. */
static BOOL mm_mixed_is_battle(IDirectDrawSurfaceImpl* primary)
{
    (void)primary;
    return mm_hd_current().mode==MM_HD_BATTLE;
}

#include "mm_battle_hud.h"
static int mm_battle_art_ready(IDirectDrawSurfaceImpl* p){
    const unsigned char* control=(const unsigned char*)0x6c4e40;
    int r[4],x,y,dim;unsigned n;
    mm_hud_load();if(!mm_hud_count)return 1;
    if(!mm_hd_readable(control,0x21))return 0;
    memcpy(r,control+0x11,16);
    if(r[0]<0 || r[1]<0 || r[2]>1280 || r[3]>720)return 0;
    for(n=0;n<mm_hud_count;++n){
        MmHudTile* t=mm_hud_tiles+n;if(t->kind!=3)continue;
        for(dim=0;dim<3;++dim)
            for(y=r[1]-8;y<=r[3]-(int)t->h+8;++y)
                for(x=r[0]-8;x<=r[2]-(int)t->w+8;++x)
                    if(mm_hud_match(t,(const unsigned char*)p->surface,p->pitch,x,y,dim))return 1;
    }
    return 0;
}

static IDirectDrawSurfaceImpl* mm_mixed_compose(IDirectDrawSurfaceImpl* primary)
{
    SIZE_T bytes;
    unsigned char* pixels;
    int x, y, sharpen, shift;
    if (!mm_mixed_enabled() || !primary || !primary->surface ||
        primary->width != 2560 || primary->height != 1440 || primary->bpp != 16 ||
        primary->pitch < 5120 || primary->pitch > 16384 ||
        mm_redraw_mode!=MM_HD_BATTLE)
        return primary;
    bytes = (SIZE_T)primary->pitch * 1440;
    if (mm_mixed_capacity < bytes)
    {
        pixels = (unsigned char*)HeapAlloc(GetProcessHeap(), 0, bytes);
        if (!pixels) return primary;
        if (mm_mixed_pixels) HeapFree(GetProcessHeap(), 0, mm_mixed_pixels);
        mm_mixed_pixels = pixels;
        mm_mixed_capacity = bytes;
    }
    memset(mm_mixed_pixels, 0, bytes);
    sharpen = mm_mixed_sharpen_level();
    shift = sharpen == 1 ? 3 : 2;
    for (y = 0; y < 720; ++y)
    {
        const unsigned short* src = (const unsigned short*)((const unsigned char*)primary->surface + y * primary->pitch);
        const unsigned short* above = y ? (const unsigned short*)((const unsigned char*)primary->surface + (y - 1) * primary->pitch) : src;
        const unsigned short* below = y < 719 ? (const unsigned short*)((const unsigned char*)primary->surface + (y + 1) * primary->pitch) : src;
        unsigned short* dst0 = (unsigned short*)(mm_mixed_pixels + y * 2 * primary->pitch);
        unsigned short* dst1 = (unsigned short*)(mm_mixed_pixels + (y * 2 + 1) * primary->pitch);
        for (x = 0; x < 1280; ++x)
        {
            unsigned short c = src[x];
            if (!sharpen)
            {
                dst0[x * 2] = dst0[x * 2 + 1] = c;
                dst1[x * 2] = dst1[x * 2 + 1] = c;
            }
            else
            {
                unsigned short left = x ? src[x - 1] : c;
                unsigned short right = x < 1279 ? src[x + 1] : c;
                dst0[x * 2] = x && y ? mm_mixed_sharpen_pixel(c, left, above[x], shift) : c;
                dst0[x * 2 + 1] = y && x < 1279 ? mm_mixed_sharpen_pixel(c, right, above[x], shift) : c;
                dst1[x * 2] = x && y < 719 ? mm_mixed_sharpen_pixel(c, left, below[x], shift) : c;
                dst1[x * 2 + 1] = x < 1279 && y < 719 ? mm_mixed_sharpen_pixel(c, right, below[x], shift) : c;
            }
        }
    }
    mm_hud_present(primary,mm_mixed_pixels);
    mm_mixed_surface = *primary;
    mm_mixed_surface.surface = mm_mixed_pixels;
    return &mm_mixed_surface;
}

IDirectDrawSurfaceImpl* mm_mixed_present(IDirectDrawSurfaceImpl* primary)
{
    if(!mm_mixed_redraw_begin(primary))return primary;
    if(mm_epoch.ready && (mm_epoch.mode!=mm_hd_current().mode ||
       mm_epoch.signature!=mm_control_signature()) && mm_last_pixels)
        return &mm_last_surface;
    if(!mm_epoch.ready)mm_redraw_mode=mm_hd_current().mode;
    return mm_remember(mm_mixed_compose(primary));
}

POINT mm_mixed_input_point(IDirectDrawSurfaceImpl* primary, int x, int y)
{
    POINT result = { x, y };
    if (mm_mixed_enabled() && primary && primary->surface && mm_mixed_is_battle(primary))
    {
        result=mm_hd_input(mm_hd_current(),x,y);
    }
    return result;
}
#endif
#endif
