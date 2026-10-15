#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdint>
#include <cstring>
#include "layout_context.h"
namespace {
using Setup=int(__thiscall*)(void*,int,const char*,const char*,const char*);
using Load=int(__thiscall*)(void*,const char*);
Setup original;
bool hd_setup;
int __fastcall load(void* bitmap,void*,const char* filename){
    return ((Load)0x486ae0)(bitmap,hd_setup?"Bitmaps\\hd-ui\\dlgback 800x600.BMP":filename);
}
int __fastcall setup(unsigned char* dialog,void*,int event,const char* text,const char* yes,const char* no){
    auto c=mm_hd_current();bool previous=hd_setup;hd_setup=c.mode==MM_HD_UI;
    int result=original(dialog,event,text,yes,no);
    if(hd_setup && result){
        auto* info=*(int**)(dialog+0x4d);
        int width=info[1],height=info[2];
        int x=c.content_x+(c.content_width-width)/2;
        int y=c.content_y+(c.content_height-height)/2;
        *(int*)(dialog+0x59)=x;*(int*)(dialog+0x5d)=y;
        const int scale=c.font_scale,margin=30*scale;
        auto* first=*(unsigned char**)(dialog+0x25);
        auto* second=*(unsigned char**)(dialog+0x29);
        int button_top=y+height-margin;
        for(int i=0;i<2;i++){
            auto* button=i?second:first;if(!button)continue;
            auto* rect=(int*)(button+0x11);
            int w=rect[2]-rect[0]+60*(scale-1);
            int h=rect[3]-rect[1]+10*(scale-1);
            int left=second?(i?x+width-margin-w:x+margin):x+(width-w)/2;
            int r[4]={left,y+height-margin-h,left+w,y+height-margin};
            // Already registered by native setup; RECT setter re-registers it.
            memcpy(button+0x11,r,sizeof(r));button_top=r[1];
        }
        int title[4]={x+margin,y+margin,x+width-margin,button_top-margin};
        memcpy(dialog+0x3d,title,sizeof(title));
        int bounds[4]={0,0,c.output_width,c.output_height};
        memcpy(dialog+0x11,bounds,sizeof(bounds));
    }
    hd_setup=previous;return result;
}
}
extern "C" bool mm_install_confirm_dialog(){
    const BYTE entry[]={0x6a,0xff,0x68,0xc2,0x1c,0x5c,0x00};
    if(memcmp((void*)0x4cf3b0,entry,7))return false;
    const unsigned calls[]={0x4cf45e,0x4cf491};
    for(auto site:calls)if(*(BYTE*)site!=0xe8 || site+5+*(int32_t*)(site+1)!=0x486ae0)return false;
    auto* trampoline=(BYTE*)VirtualAlloc(nullptr,12,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
    if(!trampoline)return false;
    memcpy(trampoline,entry,7);trampoline[7]=0xe9;
    *(int32_t*)(trampoline+8)=(int32_t)(0x4cf3b7-(uintptr_t)(trampoline+12));original=(Setup)trampoline;
    const unsigned sites[]={0x4cf45e,0x4cf491,0x4cf3b0};
    for(int i=0;i<3;i++){
        auto site=sites[i];int length=i==2?7:5;DWORD old,unused;
        if(!VirtualProtect((void*)site,length,PAGE_EXECUTE_READWRITE,&old))return false;
        BYTE code[]={BYTE(i==2?0xe9:0xe8),0,0,0,0,0x90,0x90};
        *(int32_t*)(code+1)=(int32_t)((uintptr_t)(i==2?(void*)setup:(void*)load)-site-5);
        memcpy((void*)site,code,length);FlushInstructionCache(GetCurrentProcess(),(void*)site,length);
        VirtualProtect((void*)site,length,old,&unused);
    }
    return true;
}
