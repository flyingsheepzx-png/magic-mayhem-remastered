// Campaign families still using 1.0 geometry. All sites are checked before patching.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdint>
#include <cstring>
#include <string>
#include "layout_context.h"

namespace {
using SurfaceFn=int(__thiscall*)(void*,DWORD*,const char*,int);
using BitmapFn=int(__thiscall*)(void*,const char*,int,int);
using JpegFn=int(__thiscall*)(void*,const char*);
using PngFn=int(__fastcall*)(void*,void*,const char*);
using SpeechFn=void(__thiscall*)(void*,unsigned char*);
void* speech_original;
bool speech_hd;
PngFn png;

bool ui(){return mm_hd_current().mode==MM_HD_UI;}
void __fastcall spritebar_clip(int left,int top,int right,int bottom){
    using Clip=void(__fastcall*)(int,int,int,int);
    if(ui()){
        // Native SpriteBar installs a legacy 1280x720 clip despite a native
        // full-size UI target. Use the current target, never a design constant.
        auto target=(unsigned char*)0x6a49e0;
        right=*(int*)(target+0x10);bottom=*(int*)(target+0x14);
    }
    ((Clip)0x57dc60)(left,top,right,bottom);
}
int scale(){return mm_hd_profile(0).font_scale;}
int __fastcall mini_surface(void* image,void*,DWORD* desc,const char* file,int line){
    DWORD copy[27];memcpy(copy,desc,sizeof(copy));
    if(ui()){auto c=mm_hd_profile(0);copy[2]=c.output_height;copy[3]=c.output_width;}
    return ((SurfaceFn)0x58ad90)(image,copy,file,line);
}
void __fastcall mini_config(unsigned char* owner,void*,const char* filename){
    using ConfigFn=void(__thiscall*)(void*,const char*);
    auto vtable=*reinterpret_cast<unsigned**>(owner);
    ((ConfigFn)vtable[7])(owner,filename);
    if(!ui())return;
    int count=*reinterpret_cast<int*>(owner+0x57);
    auto* data=*reinterpret_cast<unsigned char**>(owner+0x3f);
    if(count<1 || count>8 || !mm_hd_readable(data,count*0x141))return;
    // These are this page's freshly parsed Rect2 values, never global controls.
    for(int i=0;i<count;i++)for(int k=0;k<4;k++){
        auto* value=reinterpret_cast<int*>(data+i*0x141+0x14+k*4);
        *value*=scale();
    }
}
__declspec(naked) void mini_config_call(){__asm{
    mov ecx,esi
    jmp mini_config
}}
int __fastcall mini_bitmap(void* image,void*,const char* filename,int x,int y){
    if(ui())return ((BitmapFn)0x58d280)(image,
        "Interface\\MiniMenu\\hd-ui\\Realm View Mini Menu 800-600.BMP",x*scale(),y*scale());
    return ((BitmapFn)0x58d280)(image,filename,x,y);
}
int __fastcall speech_portrait_surface(void* image,void*,DWORD* desc,const char* file,int line){
    DWORD copy[27];memcpy(copy,desc,sizeof(copy));
    if(speech_hd){copy[2]*=scale();copy[3]*=scale();}
    return ((SurfaceFn)0x58ad90)(image,copy,file,line);
}
int __fastcall speech_jpeg(void* image,void*,const char* filename){
    if(!png)png=(PngFn)GetProcAddress(GetModuleHandleA("png_pages.dll"),"@mm_png_page@12");
    if(speech_hd && png){
        std::string path(filename);auto index=path.find("800x600");
        if(index!=std::string::npos){
            path.replace(index,7,"hd-ui");
            int result=png(image,nullptr,path.c_str());if(result)return result;
        }
    }
    return ((JpegFn)0x58d320)(image,filename);
}
void __fastcall speech_setup(void* controller,void*,unsigned char* descriptor){
    int saved[20]{};int* box=nullptr;bool previous=speech_hd;
    if(mm_hd_readable(descriptor,0x3d) && descriptor[0x30] && ui()){
        int index=*reinterpret_cast<int*>(descriptor+0xc)-1;
        int count=*reinterpret_cast<int*>(0x6f4788);
        auto* data=*reinterpret_cast<unsigned char**>(0x6f4784);
        // Campaign tutorials use boxes 1..3; leave world speech and battle alone.
        if(index>=0 && index<3 && index<count && mm_hd_readable(data+index*0x50,0x50)){
            box=reinterpret_cast<int*>(data+index*0x50);memcpy(saved,box,sizeof(saved));
            for(int k=0;k<18;k++)if(box[k]!=-1)box[k]*=scale();
            speech_hd=true;
        }
    }
    ((SpeechFn)speech_original)(controller,descriptor);
    if(box)memcpy(box,saved,sizeof(saved));
    speech_hd=previous;
}
struct Immediate {unsigned address,before,after;};
bool write(unsigned address,const void* data,size_t length){
    DWORD old=0,unused=0;if(!VirtualProtect((void*)address,length,PAGE_EXECUTE_READWRITE,&old))return false;
    memcpy((void*)address,data,length);FlushInstructionCache(GetCurrentProcess(),(void*)address,length);
    return VirtualProtect((void*)address,length,old,&unused)!=0;
}
bool relative(unsigned address,void* target,BYTE opcode,int length=5){
    BYTE bytes[7]={opcode,0,0,0,0,0x90,0x90};
    *reinterpret_cast<int32_t*>(bytes+1)=(int32_t)((uintptr_t)target-address-5);
    return write(address,bytes,length);
}
}
extern "C" bool mm_install_campaign_ui(){
    char enabled[4]{};GetEnvironmentVariableA("MM_PROBE_MIXED_FONTS",enabled,sizeof(enabled));
    if(strcmp(enabled,"1"))return true;
    // Fixed full-screen page backing/interaction and character portrait shim.
    const Immediate fields[]={
        {0x4b4452,1120,2400},{0x4b4465,600,1320},
        {0x473de2,1120,2400},{0x473df5,600,1320},
        {0x473e38,1119,2399},{0x473e51,599,1319},
        {0x4b5b51,800,1760},{0x4b5b77,600,1320},{0x5c42e4,160,320},
        // Heading bypasses page cfg: original 800x600 design -> UI content.
        {0x5da230,50,440},{0x5da234,36,86},{0x5da238,749,2118},{0x5da23c,76,182},
    };
    struct Call{unsigned site,target;void* hook;};
    const Call calls[]={
        {0x4dd718,0x57dc60,(void*)spritebar_clip},
        {0x4b21c7,0x58ad90,(void*)mini_surface},
        {0x4b26d9,0x58d280,(void*)mini_bitmap},
        {0x573465,0x58ad90,(void*)speech_portrait_surface},
        {0x5733ba,0x58d320,(void*)speech_jpeg},
        {0x5734f3,0x58d320,(void*)speech_jpeg},
    };
    for(auto f:fields)if(*(unsigned*)f.address!=f.before)return false;
    for(auto c:calls)if(*(BYTE*)c.site!=0xe8 || c.site+5+*(int32_t*)(c.site+1)!=c.target)return false;
    if(memcmp((void*)0x4b221f,"\x8b\xce\xff\x50\x1c",5) ||
       memcmp((void*)0x572f30,"\x6a\xff\x68\x3b\x2c\x5c\x00",7))return false;
    // The launcher injects png_pages after this module; resolve its export on use.
    auto* trampoline=(BYTE*)VirtualAlloc(nullptr,12,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
    if(!trampoline)return false;
    memcpy(trampoline,(void*)0x572f30,7);trampoline[7]=0xe9;
    *(int32_t*)(trampoline+8)=(int32_t)(0x572f37-(uintptr_t)(trampoline+12));
    speech_original=trampoline;
    for(auto f:fields)if(!write(f.address,&f.after,4))return false;
    for(auto c:calls)if(!relative(c.site,c.hook,0xe8))return false;
    return relative(0x4b221f,(void*)mini_config_call,0xe8) &&
        relative(0x572f30,(void*)speech_setup,0xe9,7);
}
