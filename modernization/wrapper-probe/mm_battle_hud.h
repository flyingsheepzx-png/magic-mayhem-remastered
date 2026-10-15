/* Full-output HUD artwork; native scene, control geometry and input untouched. */
#include "hud_overlay_core.h"
static MmHudTile mm_hud_tiles[256];
static unsigned mm_hud_count;
static unsigned char* mm_hud_data;
static int mm_hud_attempted;
typedef struct MmHudCached {const void* owner;int tile,x,y,dim,frame,state,rect[4];DWORD retry;} MmHudCached;
static MmHudCached mm_hud_cache[400];
static void mm_hud_load(void){
    HANDLE file;DWORD bytes,got=0;unsigned char* p;unsigned i;
    if(mm_hud_attempted)return;mm_hud_attempted=1;
    file=CreateFileA("Sprites\\battle-hud.bin",GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if(file==INVALID_HANDLE_VALUE)return;
    bytes=GetFileSize(file,NULL);
    if(bytes<12 || bytes>16*1024*1024){CloseHandle(file);return;}
    mm_hud_data=(unsigned char*)HeapAlloc(GetProcessHeap(),0,bytes);
    if(!mm_hud_data){CloseHandle(file);return;}
    if(!ReadFile(file,mm_hud_data,bytes,&got,NULL) || got!=bytes){CloseHandle(file);return;}
    CloseHandle(file);p=mm_hud_data;
    if(memcmp(p,"HDH1",4) || *(unsigned*)(p+4)!=1 || *(unsigned*)(p+8)>256)return;
    mm_hud_count=*(unsigned*)(p+8);p+=12;
    for(i=0;i<mm_hud_count;i++){
        MmHudTile* t=mm_hud_tiles+i;unsigned size,j;
        if(p+108>mm_hud_data+bytes)goto invalid;
        t->kind=*(unsigned*)p;t->w=*(unsigned*)(p+4);t->h=*(unsigned*)(p+8);
        if(t->kind<1 || t->kind>3 || !t->w || !t->h || t->w>164 || t->h>80)goto invalid;
        size=t->w*t->h;memcpy(t->anchors,p+12,96);p+=108;
        for(j=0;j<24;j++)if(t->anchors[j]>=size)goto invalid;
        if(p+size*11>mm_hud_data+bytes)goto invalid;
        t->low=(const unsigned short*)p;p+=size*2;t->mask=p;p+=size;
        t->high=(const unsigned short*)p;p+=size*8;
    }
    if(p!=mm_hud_data+bytes)goto invalid;
    return;
invalid:mm_hud_count=0;
}
static void mm_hud_present(IDirectDrawSurfaceImpl* primary,unsigned char* destination){
    int count=*(int*)MM_HD_CONTROL_COUNT,i;const unsigned char* src=(const unsigned char*)primary->surface;
    mm_hud_load();if(!mm_hud_count || count<=0 || count>400)return;
    for(i=0;i<count;i++){
        const unsigned char* control=((const unsigned char**)MM_HD_CONTROL_TABLE)[i];
        unsigned v,kind,n;const int* r;MmHudCached* cache=mm_hud_cache+i;int found=0,frame=0,state=0;
        if(!mm_hd_readable(control,0x21))continue;
        v=*(unsigned*)control;kind=(v==0x5c6e38 || v==0x5c5c2c)?1:v==0x5c6e4c?2:0;
        if(!kind)continue;r=(const int*)(control+0x11);
        if(kind==2){
            if(!mm_hd_readable(control,0xb9))continue;
            frame=*(const int*)(control+0xb5);state=*(const int*)(control+0x39)^*(const int*)(control+0x3d);
            if(frame<0)continue;
        }
        if(r[0]<0 || r[1]<0 || r[2]>1280 || r[3]>720 || r[2]<=r[0] || r[3]<=r[1])continue;
        // Unknown/occluded artwork falls back to native pixels. Avoid scanning
        // every empty HUD slot on every rendered frame; spell/state changes
        // invalidate this negative cache immediately.
        if(cache->owner==control && cache->frame==frame && cache->state==state && !memcmp(cache->rect,r,16) && cache->tile<0 &&
           (LONG)(GetTickCount()-cache->retry)<0)continue;
        if(cache->owner==control && cache->frame==frame && cache->state==state && !memcmp(cache->rect,r,16) && cache->tile>=0 && (unsigned)cache->tile<mm_hud_count &&
           mm_hud_match(mm_hud_tiles+cache->tile,src,primary->pitch,cache->x,cache->y,cache->dim))found=1;
        else{
            cache->owner=control;cache->tile=-1;cache->frame=frame;cache->state=state;cache->retry=GetTickCount()+500;memcpy(cache->rect,r,16);
            for(n=0;n<mm_hud_count && !found;n++){
                MmHudTile* t=mm_hud_tiles+n;int x,y,dim;
                if(t->kind!=kind && !(kind==1 && v==0x5c6e38 && t->kind==3))continue;
                for(dim=0;dim<3 && !found;dim++)
                    for(y=r[1]-8;y<=r[3]-(int)t->h+8 && !found;y++)
                        for(x=r[0]-8;x<=r[2]-(int)t->w+8;x++)
                            if(mm_hud_match(t,src,primary->pitch,x,y,dim)){
                                cache->tile=n;cache->x=x;cache->y=y;cache->dim=dim;found=1;break;
                            }
            }
        }
        if(found){
            MmHudTile* chosen=mm_hud_tiles+cache->tile;
            mm_hud_paint(chosen,src,primary->pitch,destination,primary->pitch,cache->x,cache->y,cache->dim);
            if(chosen->kind==3)for(n=0;n<mm_hud_count;n++){
                MmHudTile* t=mm_hud_tiles+n;
                if(t!=chosen && t->kind==3){
                    int offsets[3]={0,-1,1},k;
                    // Native alive/dead halves differ by one logical pixel.
                    // Source verification selects the correct half and offset.
                    for(k=0;k<3;k++)if(mm_hud_match(t,src,primary->pitch,cache->x+offsets[k],cache->y,cache->dim)){
                        mm_hud_paint(t,src,primary->pitch,destination,primary->pitch,cache->x+offsets[k],cache->y,cache->dim);break;
                    }
                }
            }
        }
    }
}
