// Opt-in mixed UI font selector for the hash-gated 531ca844 engine candidate.
// Preserve the global object addresses used by the Chinese translation module.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include "layout_context.h"
#include "ui_geometry.h"

namespace {
constexpr unsigned addresses[]={0x6b0400,0x656680,0x6df1c0,0x6a5138};
constexpr const char* paths[]={"Sprites\\mixed-original\\heading text 800.sft",
    "Sprites\\mixed-original\\body text 800.sft","Sprites\\mixed-original\\Tooltip Text.sft",
    "Sprites\\mixed-original\\yellowtext.sft"};
constexpr int heights[]={64,44,30,28};
struct Font { unsigned large[6],small[6]; int large_height,small_height; };
Font fonts[4]{};
unsigned char originals[4][0xe3c]{};
volatile unsigned* chinese_scale;
bool initialized;
int selected_mode=-1;
void* draw_target;
void* wrapped_target;
void* measure_target;
unsigned scanner_layout_width;
// Software cursor backing/dirty/restore surfaces must span the full primary.
// Battle input remains 1280x720 through the wrapper's existing mode transform.
bool expand_cursor_surface(){
    constexpr unsigned sites[]={0x4a45ff,0x4a460f,0x4a49ad,0x4a49c3,
        0x4a4b27,0x4a4b4d,0x4a4c79,0x4a4ca0,0x4e4231,0x4e4246};
    for(unsigned i=0;i<10;i++)if(*reinterpret_cast<unsigned*>(sites[i])!=(i%2?600u:1120u))return false;
    for(unsigned i=0;i<10;i++){
        DWORD old=0,unused=0;
        if(!VirtualProtect((void*)sites[i],4,PAGE_EXECUTE_READWRITE,&old))return false;
        *reinterpret_cast<unsigned*>(sites[i])=i%2?1320u:2400u;
        FlushInstructionCache(GetCurrentProcess(),(void*)sites[i],4);
        VirtualProtect((void*)sites[i],4,old,&unused);
    }
    return true;
}
// Scanner storage stride remains the actual 2560-wide primary. Only its
// layout width uses the battle profile; the native RECT setter then keeps
// drawing and hit testing on the same coordinates.
__declspec(naked) void scanner_width_hook(){__asm{
    mov eax,dword ptr [scanner_layout_width]
    push 554b0ch
    ret
}}
__declspec(naked) void scanner_draw_width_hook(){__asm{
    mov eax,dword ptr [scanner_layout_width]
    push 554901h
    ret
}}
// Main +0xeb aliases secondary +0xca: physical storage width, not HUD width.
__declspec(naked) void scanner_click_width_hook(){__asm{
    mov ebp,dword ptr [scanner_layout_width]
    push 555f23h
    ret
}}
// Unit-marker projection has separate anchors from background/rectangle draw.
// +0xeb must remain physical row stride elsewhere in these native routines.
__declspec(naked) void scanner_units_width_a_hook(){__asm{
    mov eax,dword ptr [scanner_layout_width]
    push 552f2fh
    ret
}}
__declspec(naked) void scanner_units_width_b_hook(){__asm{
    mov eax,dword ptr [scanner_layout_width]
    push 5532ffh
    ret
}}
__declspec(naked) void scanner_refresh_width_hook(){__asm{
    mov eax,dword ptr [scanner_layout_width]
    mov ecx,dword ptr [esi+0e2h]
    push 555b96h
    ret
}}
void* sprite_draw_original;
unsigned char* port_icon_file;
unsigned char port_icon_sprite[0x28];
unsigned original_icon_sprite;
bool port_icon_attempted;
bool readable(const void* pointer,size_t bytes);
bool load_port_icons(unsigned char* source){
    // Portmanteau also uses mitems/Talisman containers in the same vtable.
    // Reject those before caching an attempt or substituting SplIcons data.
    if(!readable(source,0x28))return false;
    auto* file_data=*reinterpret_cast<unsigned char**>(source);
    if(!readable(file_data,24) || memcmp(file_data,"SPR\0",4) ||
       *reinterpret_cast<unsigned*>(file_data+12)!=234)return false;
    if(*reinterpret_cast<unsigned*>(source+0x20)!=0)return false;
    if(port_icon_attempted){
        if(!port_icon_file)return false;
        // Page controls and their Sprite objects are recreated after returning
        // from battle. Cache the immutable pixels, never the owner's address.
        memcpy(port_icon_sprite,source,sizeof(port_icon_sprite));
        *reinterpret_cast<unsigned*>(port_icon_sprite)=reinterpret_cast<unsigned>(port_icon_file);
        *reinterpret_cast<unsigned*>(port_icon_sprite+8)=reinterpret_cast<unsigned>(port_icon_file+24);
        *reinterpret_cast<unsigned*>(port_icon_sprite+12)=reinterpret_cast<unsigned>(port_icon_file+24+234*4);
        original_icon_sprite=reinterpret_cast<unsigned>(source);
        return true;
    }
    port_icon_attempted=true;
    HANDLE file=CreateFileA("Sprites\\port-icons.spr",GENERIC_READ,FILE_SHARE_READ,
        nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE)return false;
    DWORD length=GetFileSize(file,nullptr);
    if(length<1000 || length>8*1024*1024){CloseHandle(file);return false;}
    auto* data=(unsigned char*)HeapAlloc(GetProcessHeap(),0,length);
    DWORD got=0;
    bool ok=data && ReadFile(file,data,length,&got,nullptr) && got==length;
    CloseHandle(file);
    if(!ok){if(data)HeapFree(GetProcessHeap(),0,data);return false;}
    const unsigned* head=(const unsigned*)data;
    if(memcmp(data,"SPR\0",4) || head[1]!=length || head[2]!=4 ||
       head[3]!=234 || head[4]!=0 || head[5]!=0){
        HeapFree(GetProcessHeap(),0,data);return false;
    }
    const unsigned* offsets=(const unsigned*)(data+24);
    if(offsets[0]!=0 || offsets[233]>=length-24-234*4){
        HeapFree(GetProcessHeap(),0,data);return false;
    }
    auto* original=(unsigned char*)source;
    if(!readable(original,0x28) ||
       *reinterpret_cast<unsigned*>(original+0x20)!=0){
        HeapFree(GetProcessHeap(),0,data);return false;
    }
    memcpy(port_icon_sprite,original,sizeof(port_icon_sprite));
    *reinterpret_cast<unsigned*>(port_icon_sprite)=reinterpret_cast<unsigned>(data);
    *reinterpret_cast<unsigned*>(port_icon_sprite+8)=reinterpret_cast<unsigned>(data+24);
    *reinterpret_cast<unsigned*>(port_icon_sprite+12)=reinterpret_cast<unsigned>(data+24+234*4);
    original_icon_sprite=reinterpret_cast<unsigned>(original);
    port_icon_file=data;
    return true;
}
bool portmanteau_page(){
    int count=*reinterpret_cast<int*>(MM_HD_CONTROL_COUNT);
    if(count<=0 || count>400)return false;
    auto** table=reinterpret_cast<unsigned char**>(MM_HD_CONTROL_TABLE);
    for(int i=0;i<count;i++)if(readable(table[i],4) &&
        *reinterpret_cast<unsigned*>(table[i])==0x5c77f0)return true;
    return false;
}
typedef void (__thiscall* SpriteDrawFn)(void*);
void __fastcall port_icon_draw_hook(unsigned char* control,void*){
    bool selected=false;
    if(control && *reinterpret_cast<unsigned*>(control)==0x5c77bc){
        const int* rect=reinterpret_cast<const int*>(control+0x11);
        const int x=rect[0],y=rect[1],right=rect[2],bottom=rect[3];
        const int frame=*reinterpret_cast<int*>(control+0x59);
        MmHdLayoutContext c=mm_hd_current();
        selected=mm_ui_port_icon(c.mode==MM_HD_UI,portmanteau_page(),
            mm_ui_fit(c.output_width,c.output_height),c.font_scale,x,y,right,bottom,frame);
    }
    if(selected){
        auto* field=reinterpret_cast<unsigned*>(control+0x55);
        if(load_port_icons((unsigned char*)*field)){
            unsigned saved=*field;
            *field=reinterpret_cast<unsigned>(port_icon_sprite);
            ((SpriteDrawFn)sprite_draw_original)(control);
            *field=saved;
            return;
        }
    }
    ((SpriteDrawFn)sprite_draw_original)(control);
}
void __cdecl constrain_tooltip(unsigned char* tip){
    if(!tip || !*reinterpret_cast<int*>(tip+4) || mm_hd_current().mode!=MM_HD_UI)return;
    MmHdLayoutContext c=mm_hd_current();
    int rect[4];memcpy(rect,tip+0x16a,sizeof(rect));
    int width=rect[2]-rect[0],height=rect[3]-rect[1];
    if(width<=0 || height<=0 || width>c.content_width || height>c.content_height)return;
    int x=mm_ui_clamp_origin(rect[0],width,c.content_x,c.content_x+c.content_width);
    int y=mm_ui_clamp_origin(rect[1],height,c.content_y,c.content_y+c.content_height);
    rect[0]=x;rect[1]=y;rect[2]=x+width;rect[3]=y+height;
    memcpy(tip+0x16a,rect,sizeof(rect));
    // Native blit reads x from the tooltip surface object's +0x20 field.
    *reinterpret_cast<int*>(tip+0x144)=x;*reinterpret_cast<int*>(tip+0x148)=y;
}
__declspec(naked) void tooltip_destination_hook(){__asm{
    pushfd
    pushad
    push esi
    call constrain_tooltip
    add esp,4
    popad
    popfd
    mov edi,dword ptr ds:[6e1ee4h]
    push 4db938h
    ret
}}
int tooltip_mode=-1;
bool tooltip_ready;
struct TipImmediate { unsigned address; int small,large,bytes; };
constexpr TipImmediate tip_immediates[]={
    {0x4db837,600,1320,4},{0x4db88f,1120,2400,4},
    {0x4db8ba,600,1320,4},
    {0x4db832,20,40,1},{0x4db845,20,40,1},
    {0x4dba99,8,16,1},{0x4dbae3,12,24,1},
    {0x4dbaed,12,24,1},{0x4dbaff,12,24,1},
    {0x4dbb09,12,24,1},{0x4dbb39,8,16,1},
};
void select_tooltip(int mode){
    if(!tooltip_ready)return;
    auto* tip=reinterpret_cast<unsigned char*>(0x657fe8);
    *reinterpret_cast<int*>(tip+0x10)=mode==1?300:600;
    *reinterpret_cast<int*>(tip+0xc)=mode==1?15:30;
    if(mode==tooltip_mode)return;
    // These immediate fields belong only to the global tooltip layout path.
    // Keep battle's original bounds and padding; independent pages use 2x.
    for(const auto& p:tip_immediates){
        void* site=reinterpret_cast<void*>(p.address);DWORD old=0,unused=0;
        if(!VirtualProtect(site,p.bytes,PAGE_EXECUTE_READWRITE,&old))return;
        int value=mode==1?p.small:p.large;
        memcpy(site,&value,p.bytes);FlushInstructionCache(GetCurrentProcess(),site,p.bytes);
        VirtualProtect(site,p.bytes,old,&unused);
    }
    // The tooltip owns an offscreen surface allocated from nominal width.
    // Recreate it on a page-mode transition, otherwise the 600px layout is
    // blitted from a stale 300px surface and its right half gets clipped.
    if(*reinterpret_cast<unsigned*>(tip+0x128)){
        typedef void (__thiscall* SurfaceFn)(void*);
        ((SurfaceFn)0x58b3e0)(tip+0x124);
        ((SurfaceFn)0x4db650)(tip);
        *reinterpret_cast<int*>(tip+4)=0;
        *reinterpret_cast<int*>(tip+0x17a)=0;
    }
    tooltip_mode=mode;
}
bool readable(const void* pointer,size_t bytes){
    MEMORY_BASIC_INFORMATION m{};
    if(!pointer || !VirtualQuery(pointer,&m,sizeof(m)) || m.State!=MEM_COMMIT ||
       (m.Protect&(PAGE_NOACCESS|PAGE_GUARD)))return false;
    uintptr_t end=(uintptr_t)pointer+bytes;
    return end>=(uintptr_t)pointer && end<=(uintptr_t)m.BaseAddress+m.RegionSize;
}
bool battle_page(){return mm_hd_current().mode==MM_HD_BATTLE;}
bool initialize(){
    if(initialized)return true;
    typedef int (__thiscall* LoadFn)(void*,const char*,int);
    for(int i=0;i<4;i++){
        auto* object=reinterpret_cast<unsigned char*>(addresses[i]);
        auto* data=*reinterpret_cast<unsigned char**>(object);
        if(!readable(data,40) || memcmp(data,"SFT\0",4) ||
           *reinterpret_cast<int*>(data+16)!=heights[i])return false;
        memcpy(originals[i],object,sizeof(originals[i]));
        memset(originals[i],0,24);
        if(!((LoadFn)0x4a5ae0)(originals[i],paths[i],2))return false;
        auto* small=*reinterpret_cast<unsigned char**>(originals[i]);
        if(!readable(small,40) || *reinterpret_cast<int*>(small+16)*2!=heights[i])return false;
        memcpy(fonts[i].large,object,24);memcpy(fonts[i].small,originals[i],24);
        fonts[i].large_height=*reinterpret_cast<int*>(object+0x220);
        fonts[i].small_height=*reinterpret_cast<int*>(originals[i]+0x220);
    }
    initialized=true;return true;
}
void __cdecl select_fonts(unsigned caller){
    if(!initialized && !initialize())return;
    // The control-limit counter is cached on a 48x22 battle surface while
    // Load Game still owns the page controls. Select its battle font explicitly.
    int mode=(caller==0x4de797 || battle_page())?1:2;
    select_tooltip(mode);
    if(mode==selected_mode)return;
    for(int i=0;i<4;i++){
        auto* object=reinterpret_cast<unsigned char*>(addresses[i]);
        memcpy(object,mode==1?fonts[i].small:fonts[i].large,24);
        *reinterpret_cast<int*>(object+0x220)=mode==1?fonts[i].small_height:fonts[i].large_height;
        *reinterpret_cast<int*>(object+0x230)=mode==1?2:4;
    }
    if(chinese_scale)*chinese_scale=mode;
    selected_mode=mode;
    char flag[4]{};
    if(GetEnvironmentVariableA("MM_PROBE_FONT_LOG",flag,sizeof(flag)) && flag[0]=='1'){
        FILE* log=nullptr;
        if(!fopen_s(&log,"modernization\\logs\\mixed-fonts.csv","ab") && log){
            fprintf(log,"mode,%d,heights,%d,%d,%d,%d\n",mode,
                *reinterpret_cast<int*>(*reinterpret_cast<unsigned*>(addresses[0])+16),
                *reinterpret_cast<int*>(*reinterpret_cast<unsigned*>(addresses[1])+16),
                *reinterpret_cast<int*>(*reinterpret_cast<unsigned*>(addresses[2])+16),
                *reinterpret_cast<int*>(*reinterpret_cast<unsigned*>(addresses[3])+16));
            fclose(log);
        }
    }
}
__declspec(naked) void draw_hook(){__asm{
    pushfd
    pushad
    push dword ptr [esp+36]
    call select_fonts
    add esp,4
    popad
    popfd
    jmp dword ptr [draw_target]
}}
__declspec(naked) void wrapped_hook(){__asm{
    pushfd
    pushad
    push dword ptr [esp+36]
    call select_fonts
    add esp,4
    popad
    popfd
    jmp dword ptr [wrapped_target]
}}
__declspec(naked) void measure_hook(){__asm{
    pushfd
    pushad
    push dword ptr [esp+36]
    call select_fonts
    add esp,4
    popad
    popfd
    sub esp,1ach
    jmp dword ptr [measure_target]
}}
__declspec(naked) void tooltip_measure_hook(){__asm{
    pushfd
    pushad
    push 0
    call select_fonts
    add esp,4
    popad
    popfd
    sub esp,34h
    push ebx
    push ebp
    push esi
    push edi
    push 4dba67h
    ret
}}
__declspec(naked) void tooltip_layout_hook(){__asm{
    pushfd
    pushad
    push 0
    call select_fonts
    add esp,4
    popad
    popfd
    sub esp,0ch
    push esi
    push edi
    push 4db7e5h
    ret
}}
// Loading has no battle controls. Render its bar directly on the native
// primary instead of relying on the battle compositor to enlarge it.
struct ProgressImmediate {unsigned address, small, large;};
constexpr ProgressImmediate progress_immediates[]={
    {0x4dc4eb,718,1436},{0x4dc4f3,43,86},
    {0x4dc54c,718,1436},{0x4dc554,43,86},
    {0x4dc56c,718,1436},{0x4dc578,43,86},
    {0x4dc614,718,1436},{0x4dc624,718,1436},{0x4dc62b,718,1436}
};
__declspec(naked) void progress_init_hook(){__asm{
    mov dword ptr [esp+4],562
    mov dword ptr [esp+8],1310
    sub esp,6ch
    push esi
    mov esi,ecx
    push 4dc4a6h
    ret
}}
bool patch_tip(unsigned address,void* target,int length){
    auto* site=reinterpret_cast<unsigned char*>(address);DWORD old=0,unused=0;
    if(!VirtualProtect(site,length,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char code[7]={0xe9,0,0,0,0,0x90,0x90};
    *reinterpret_cast<int*>(code+1)=(int)((uintptr_t)target-address-5);
    memcpy(site,code,length);FlushInstructionCache(GetCurrentProcess(),site,length);
    return VirtualProtect(site,length,old,&unused)!=0;
}
bool patch(unsigned address,void* target){
    auto* site=reinterpret_cast<unsigned char*>(address);DWORD old=0,unused=0;
    if(!VirtualProtect(site,6,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char code[]={0xe9,0,0,0,0,0x90};
    *reinterpret_cast<int*>(code+1)=(int)((uintptr_t)target-address-5);
    memcpy(site,code,6);FlushInstructionCache(GetCurrentProcess(),site,6);
    return VirtualProtect(site,6,old,&unused)!=0;
}
}
extern "C" bool mm_install_mixed_fonts(){
    char enabled[4]{};GetEnvironmentVariableA("MM_PROBE_MIXED_FONTS",enabled,sizeof(enabled));
    if(enabled[0]!='1' || enabled[1])return true;
    HMODULE chinese=GetModuleHandleA("chaos95.dll");
    if(!chinese)return false;
    auto* base=reinterpret_cast<unsigned char*>(chinese);
    auto* dos=reinterpret_cast<IMAGE_DOS_HEADER*>(base);
    auto* nt=reinterpret_cast<IMAGE_NT_HEADERS32*>(base+dos->e_lfanew);
    auto* section=IMAGE_FIRST_SECTION(nt);
    for(unsigned i=0;i<nt->FileHeader.NumberOfSections;i++){
        if(!memcmp(section[i].Name,".hdfb",5) && section[i].Misc.VirtualSize==32768)
            chinese_scale=reinterpret_cast<volatile unsigned*>(base+section[i].VirtualAddress+32764);
    }
    if(!chinese_scale)return false;
    if(memcmp((void*)0x554b06,"\x8b\x86\xca\x00\x00\x00",6) ||
       memcmp((void*)0x5548fb,"\x8b\x86\xca\x00\x00\x00",6) ||
       memcmp((void*)0x555f1d,"\x8b\xab\xeb\x00\x00\x00",6) ||
       memcmp((void*)0x555b90,"\x8b\x8e\xe2\x00\x00\x00",6))return false;
    scanner_layout_width=mm_hd_profile(1).content_width;
    // v38 already redirects progress through its checked disk shim.
    constexpr unsigned char progress_entry[]={0xe9,0x5b,0x7f,0x0e,0x00,0x90};
    constexpr unsigned char progress_shim[]={0xc7,0x44,0x24,0x04,0x19,0x01,0,0,
        0xc7,0x44,0x24,0x08,0x8f,0x02,0,0,0x83,0xec,0x6c,0x56,0x8b,0xf1};
    if(memcmp((void*)0x4dc4a0,progress_entry,sizeof(progress_entry)) ||
       memcmp((void*)0x5c4400,progress_shim,sizeof(progress_shim)))return false;
    for(const auto& p:progress_immediates)
        if(*reinterpret_cast<unsigned*>(p.address)!=p.small)return false;
    if(memcmp((void*)0x4db932,"\x8b\x3d\xe4\x1e\x6e\x00",6))return false;
    if(memcmp((void*)0x4dba60,"\x83\xec\x34\x53\x55\x56\x57",7) ||
       memcmp((void*)0x4db7e0,"\x83\xec\x0c\x56\x57",5))return false;
    for(const auto& p:tip_immediates)
        if(memcmp((void*)p.address,&p.small,p.bytes))return false;
    if(*reinterpret_cast<unsigned*>(0x5c77cc)!=0x5790e0)return false;
    auto* draw=reinterpret_cast<unsigned char*>(0x4a5ce0);
    auto* wrap=reinterpret_cast<unsigned char*>(0x4a6190);
    // Retain the translation's push/ret entry shims and their side effects.
    if(draw[0]!=0x68 || draw[5]!=0xc3 || wrap[0]!=0x68 || wrap[5]!=0xc3 ||
       *reinterpret_cast<unsigned*>(draw+1)!=(uintptr_t)base+0x18f0 ||
       *reinterpret_cast<unsigned*>(wrap+1)!=(uintptr_t)base+0x191c ||
       memcmp((void*)0x4a6630,"\x81\xec\xac\x01\x00\x00",6))return false;
    draw_target=(void*)*(unsigned*)(draw+1);wrapped_target=(void*)*(unsigned*)(wrap+1);
    measure_target=(void*)0x4a6636;
    // Delay file loading until a text call on the engine thread.
    tooltip_ready=true;
    sprite_draw_original=reinterpret_cast<void*>(0x5790e0);
    DWORD vtable_old=0,vtable_unused=0;
    if(!VirtualProtect((void*)0x5c77cc,4,PAGE_READWRITE,&vtable_old))return false;
    *reinterpret_cast<unsigned*>(0x5c77cc)=reinterpret_cast<unsigned>(port_icon_draw_hook);
    VirtualProtect((void*)0x5c77cc,4,vtable_old,&vtable_unused);
    for(const auto& p:progress_immediates){
        DWORD old=0,unused=0;
        if(!VirtualProtect((void*)p.address,4,PAGE_EXECUTE_READWRITE,&old))return false;
        *reinterpret_cast<unsigned*>(p.address)=p.large;
        FlushInstructionCache(GetCurrentProcess(),(void*)p.address,4);
        VirtualProtect((void*)p.address,4,old,&unused);
    }
    if(memcmp((void*)0x552f29,"\x8b\x86\xeb\x00\x00\x00",6) ||
       memcmp((void*)0x5532f9,"\x8b\x86\xeb\x00\x00\x00",6))return false;
    return expand_cursor_surface() && patch(0x552f29,scanner_units_width_a_hook) && patch(0x5532f9,scanner_units_width_b_hook) && patch(0x555f1d,scanner_click_width_hook) && patch(0x554b06,scanner_width_hook) && patch(0x5548fb,scanner_draw_width_hook) && patch(0x555b90,scanner_refresh_width_hook) &&
        patch(0x4dc4a0,progress_init_hook) && patch(0x4a5ce0,draw_hook) && patch(0x4a6190,wrapped_hook) && patch(0x4a6630,measure_hook) &&
        patch_tip(0x4dba60,tooltip_measure_hook,7) && patch_tip(0x4db7e0,tooltip_layout_hook,5) && patch_tip(0x4db932,tooltip_destination_hook,6);
}
