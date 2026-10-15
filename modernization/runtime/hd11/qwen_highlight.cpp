#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstring>
#include "layout_context.h"
extern "C" int mm_qwen_highlight(void* destination,RECT* target,const char* world,unsigned region){
    using Surface=int(__thiscall*)(void*,DWORD*,const char*,int);
    using Png=int(__fastcall*)(void*,void*,const char*);
    using Destroy=void(__thiscall*)(void*);
    using Blt=HRESULT(WINAPI*)(void*,RECT*,void*,RECT*,DWORD,void*);
    static unsigned char image[0x32]{};static char previous[256]{};
    if(!world || !region || region>32 || !mm_hd_readable(world,16))return 0;
    if(strcmp(world,"Celtic") && strcmp(world,"Greek") && strcmp(world,"Medieval"))return 0;
    char filename[256];sprintf_s(filename,"Interface\\RealmViewer\\hd-selected\\%s_%02u.PNG",world,region);
    if(strcmp(filename,previous)){
        auto png=(Png)GetProcAddress(GetModuleHandleA("png_pages.dll"),"@mm_png_page@12");if(!png)return 0;
        if(*(void**)(image+8))((Destroy)0x58b3e0)(image);
        memset(image,0,sizeof(image));previous[0]=0;
        DWORD desc[27]{};desc[0]=108;desc[1]=7;desc[2]=1440;desc[3]=2560;desc[26]=0x840;
        if(!((Surface)0x58ad90)(image,desc,__FILE__,__LINE__) || !png(image,nullptr,filename))return 0;
        strcpy_s(previous,filename);
    }
    auto src=*(void**)(image+8);auto dst=*(void**)((unsigned char*)destination+8);if(!src||!dst)return 0;
    // Identical native source/destination rectangle: no extra scaling or key fringe.
    auto table=*(void***)dst;
    return SUCCEEDED(((Blt)table[5])(dst,target,src,target,0x01000000,nullptr))?1:0;
}
