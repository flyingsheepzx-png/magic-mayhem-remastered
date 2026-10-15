// Isolated single-player Portmanteau and battle casting trial.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <array>
#include <cstdio>
#include <cstring>
#include <regex>
#include <string>

namespace {
constexpr unsigned kHandler=0x578610;
unsigned handler_resume=0x578617;
constexpr unsigned char kOriginal[]={0x53,0x56,0x8b,0x44,0x24,0x10,0x57};
constexpr char kKeys[]="QWERASDFZXCV";
constexpr char kPath[]="modernization\\config\\qol-hotkeys.json";
struct Slot { int tray=-1, index=-1; };
std::array<Slot,12> bindings{};
void* port_ui=nullptr;
bool loaded=false;
bool config_error=false;
void trace_event(void* ui,unsigned msg,unsigned key,unsigned lparam) {
    char enabled[8]{};
    if(!GetEnvironmentVariableA("MM_QOL_TRACE",enabled,sizeof(enabled)))return;
    FILE* f=nullptr;
    if(fopen_s(&f,"modernization\\logs\\qol-input-events.txt","ab") || !f)return;
    auto* b=static_cast<unsigned char*>(ui);
    POINT p{};GetCursorPos(&p);
    HWND h=*reinterpret_cast<HWND*>(0x656614);
    BOOL converted=ScreenToClient(h,&p);
    fprintf(f,"ui=%p msg=%x key=%x lp=%x hwnd=%p converted=%d mouse=%ld,%ld native=%d,%d counts=%d,%d,%d\n",
        ui,msg,key,lparam,h,converted,p.x,p.y,*reinterpret_cast<int*>(b+0x9c),*reinterpret_cast<int*>(b+0xa0),
        *reinterpret_cast<int*>(b+0x84),*reinterpret_cast<int*>(b+0x88),*reinterpret_cast<int*>(b+0x8c));
    for(int t=0;t<3;t++){
        int n=*reinterpret_cast<int*>(b+0x84+4*t);
        auto* c=*reinterpret_cast<unsigned char**>(b+0x218+4*t);
        if(n<0 || n>21 || !c)continue;
        for(int s=0;s<n;s++){
            auto* r=reinterpret_cast<RECT*>(c+s*0x86+0x11);
            fprintf(f,"slot=%d,%d rect=%ld,%ld,%ld,%ld cached=%d live=%d\n",t,s,r->left,r->top,r->right,r->bottom,
                *reinterpret_cast<int*>(b+0xb4+0x54*t+4*s),*reinterpret_cast<int*>(c+s*0x86+0x7e));
        }
    }
    fclose(f);
}

bool same(Slot a,Slot b) {return a.tray==b.tray && a.index==b.index;}
bool valid(Slot a) {return a.tray>=0 && a.tray<3 && a.index>=0 && a.index<21;}
int key_index(unsigned key) {
    if(key==0 || key>255)return -1;
    if(key>='a' && key<='z')key-=32;
    const char* found=strchr(kKeys,static_cast<char>(key));
    return found?static_cast<int>(found-kKeys):-1;
}
bool load() {
    if(loaded)return !config_error;
    loaded=true;
    FILE* file=nullptr;
    if(fopen_s(&file,kPath,"rb") || !file)return true; // missing means unbound
    std::string data;
    char chunk[512];size_t n=0;
    while((n=fread(chunk,1,sizeof(chunk),file))>0) {
        data.append(chunk,n);
        if(data.size()>8192){config_error=true;break;}
    }
    if(ferror(file))config_error=true;
    fclose(file);
    if(config_error)return false;
    // Accept the versioned schema written by the companion layout module.
    // Reject unknown or duplicate records rather than silently discarding them.
    static const std::regex outer(R"rx(^\s*\{\s*"version"\s*:\s*1\s*,\s*"bindings"\s*:\s*\{([\s\S]*)\}\s*\}\s*$)rx");
    static const std::regex entry(R"rx(^\s*"([QWERASDFZXCV])"\s*:\s*\{\s*"tray"\s*:\s*([0-2])\s*,\s*"slot"\s*:\s*(\d{1,2})\s*\}\s*)rx");
    std::smatch match;
    if(!std::regex_match(data,match,outer)){config_error=true;return false;}
    std::string body=match[1].str();
    while(true) {
        if(body.find_first_not_of(" \t\r\n")==std::string::npos)break;
        if(!std::regex_search(body,match,entry,std::regex_constants::match_continuous)){
            config_error=true;return false;
        }
        int key=key_index(match[1].str()[0]);
        Slot slot{std::stoi(match[2].str()),std::stoi(match[3].str())};
        if(key<0 || !valid(slot) || valid(bindings[key])){config_error=true;return false;}
        for(Slot old:bindings)if(same(old,slot)){config_error=true;return false;}
        bindings[key]=slot;
        body.erase(0,match.length());
        if(body.find_first_not_of(" \t\r\n")==std::string::npos)break;
        body.erase(0,body.find_first_not_of(" \t\r\n"));
        if(body[0]!=','){config_error=true;return false;}
        body.erase(0,1);
    }
    return true;
}
bool save() {
    std::string data="{\n  \"version\": 1,\n  \"bindings\": {";
    bool first=true;
    for(int i=0;i<12;i++)if(valid(bindings[i])){
        char line[96];
        _snprintf_s(line,sizeof(line),_TRUNCATE,"%s\n    \"%c\": {\"tray\": %d, \"slot\": %d}",
                    first?"":",",kKeys[i],bindings[i].tray,bindings[i].index);
        data+=line;first=false;
    }
    data+="\n  }\n}\n";
    if(!CreateDirectoryA("modernization\\config",nullptr) && GetLastError()!=ERROR_ALREADY_EXISTS)return false;
    std::string temporary=std::string(kPath)+".tmp";
    FILE* file=nullptr;
    if(fopen_s(&file,temporary.c_str(),"wb") || !file)return false;
    bool okay=fwrite(data.data(),1,data.size(),file)==data.size() && fflush(file)==0;
    if(fclose(file))okay=false;
    if(okay)okay=MoveFileExA(temporary.c_str(),kPath,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;
    if(!okay)DeleteFileA(temporary.c_str());
    return okay;
}
bool hovered_equipped_slot(void* ui,Slot* result) {
    auto* mouse=static_cast<unsigned char*>(ui);
    POINT native{*reinterpret_cast<int*>(mouse+0x9c),*reinterpret_cast<int*>(mouse+0xa0)};
    int width=*reinterpret_cast<int*>(0x6a49f0),height=*reinterpret_cast<int*>(0x6a49f4);
    if(width<800 || width>1120 || height<600 || height>840 ||
       native.x<0 || native.y<0 || native.x>=width || native.y>=height)return false;
    auto* base=static_cast<unsigned char*>(ui);
    for(int tray=0;tray<3;tray++){
        int count=*reinterpret_cast<int*>(base+0x84+4*tray);
        auto* controls=*reinterpret_cast<unsigned char**>(base+0x218+4*tray);
        if(count<0 || count>21 || (count && !controls))return false;
        for(int index=0;index<count;index++){
            auto* control=controls+index*0x86;
            auto* rect=reinterpret_cast<RECT*>(control+0x11);
            if(!PtInRect(rect,native))continue;
            int spell=*reinterpret_cast<int*>(base+0xb4+0x54*tray+4*index);
            if(spell<0)return false;
            *result={tray,index};return true;
        }
    }
    return false;
}
int __cdecl on_event(void* ui,unsigned msg,unsigned key,unsigned lparam) {
    port_ui=ui;
    if(msg==WM_KEYDOWN && (key==VK_ESCAPE || key==VK_RETURN))port_ui=nullptr;
    if(msg!=WM_KEYDOWN || (lparam&(1u<<30)))return 0;
    trace_event(ui,msg,key,lparam);
    int index=key_index(key);
    if(index<0 && key!=VK_DELETE)return 0;
    if(*reinterpret_cast<int*>(0x6e1f0c)>1)return 0;
    Slot hovered;
    if(!hovered_equipped_slot(ui,&hovered))return 0;
    if(!load())return 0;
    auto old=bindings;
    if(key==VK_DELETE){
        bool changed=false;
        for(Slot& slot:bindings)if(same(slot,hovered)){slot={};changed=true;}
        if(!changed)return 1;
    }else{
        if(same(bindings[index],hovered))return 1;
        for(Slot& slot:bindings)if(same(slot,hovered))slot={};
        bindings[index]=hovered;
    }
    if(!save()){bindings=old;return 0;}
    return 1;
}
__declspec(naked) void handler_hook() {
    __asm {
        pushfd
        pushad
        // Entry uses thiscall: ECX is the Portmanteau UI, followed by
        // hwnd, message, virtual key and lParam on the stack.
        mov eax,[esp+34h]
        push eax
        mov eax,[esp+34h]
        push eax
        mov eax,[esp+34h]
        push eax
        mov eax,[esp+24h]
        push eax
        call on_event
        add esp,10h
        mov [esp+1ch],eax
        popad
        popfd
        test eax,eax
        jnz consumed
        push ebx
        push esi
        mov eax,[esp+10h]
        push edi
        jmp dword ptr [handler_resume]
    consumed:
        xor eax,eax
        ret 10h
    }
}

unsigned present_resume=0x58bf46;
bool overlay_busy=false;
// 5x7 glyphs; rows are left-to-right 5-bit masks.
constexpr unsigned char glyphs[12][7]={
 {14,17,17,17,21,18,13},{17,17,17,21,21,21,10},{31,16,16,30,16,16,31},{30,17,17,30,20,18,17},
 {14,17,17,31,17,17,17},{15,16,16,14,1,1,30},{30,17,17,17,17,17,30},{31,16,16,30,16,16,16},
 {31,1,2,4,8,16,31},{17,17,10,4,10,17,17},{14,17,16,16,16,17,14},{17,17,17,17,17,10,4}};
// Verified against all 21 live native rows in test6, not icon ordering.
constexpr int talisman_spells[21][3]={
 {6,17,8},{41,71,52},{74,73,46},{1,15,10},{3,19,14},{83,34,35},
 {54,82,79},{69,72,65},{68,80,75},{7,16,11},{2,22,13},{4,21,9},
 {43,85,86},{50,44,42},{84,88,58},{92,70,91},{81,55,62},{78,87,33},
 {38,77,76},{5,60,12},{20,18,23}};
bool readable(const void* p,size_t n){
    MEMORY_BASIC_INFORMATION m{};
    if(!p || !VirtualQuery(p,&m,sizeof(m)) || m.State!=MEM_COMMIT ||
       (m.Protect&(PAGE_GUARD|PAGE_NOACCESS)))return false;
    return reinterpret_cast<uintptr_t>(p)+n<=reinterpret_cast<uintptr_t>(m.BaseAddress)+m.RegionSize;
}
bool battle_rect(Slot slot,RECT* rect,int* icon_index=nullptr){
    auto* box=reinterpret_cast<unsigned char*>(0x6a2dd0);
    auto* unit=*reinterpret_cast<unsigned char**>(box+0x18ec);
    auto* player=reinterpret_cast<unsigned char*>(0x65b250);
    int count=*reinterpret_cast<int*>(box+0x1518);
    if(!readable(unit,0x930) || count<1 || count>26)return false;
    auto* definition=*reinterpret_cast<int**>(unit+0xac);
    if(!readable(definition,4))return false;
    if(*definition!=0 && *definition!=0x18 && *definition!=0x19 && *definition!=0x1a)return false;
    // Only the player's wizard spell list may own campaign talisman bindings.
    if(*reinterpret_cast<int*>(unit+0x7c)!=0)return false;
    int n=*reinterpret_cast<int*>(player+0x92a);
    auto* equipped=*reinterpret_cast<int**>(player+0x932);
    if(n<0 || n>63 || !readable(equipped,n*4))return false;
    int layout[3][21];memset(layout,0xff,sizeof(layout));int next[3]={};
    int counts[3];
    for(int t=0;t<3;t++){
        counts[t]=*reinterpret_cast<int*>(player+0xf0+4*t);
        if(counts[t]<0 || counts[t]>21)return false;
    }
    // Native 0x575610 restores trays in equipped-list order on a fresh load.
    for(int i=0;i<n;i++){
        if(equipped[i]==-1)break;
        for(int item=0;item<21;item++)for(int t=0;t<3;t++)if(talisman_spells[item][t]==equipped[i]){
            bool found=false;for(int s=0;s<next[t];s++)if(layout[t][s]==item)found=true;
            if(!found && next[t]<counts[t])layout[t][next[t]++]=item;
        }
    }
    // An opened Portmanteau is authoritative for in-process empty/replaced slots.
    auto* ui=reinterpret_cast<unsigned char*>(0x6f2aa0);
    if(*reinterpret_cast<unsigned char**>(ui+0x90)==player){
        for(int t=0;t<3;t++)for(int s=0;s<counts[t];s++){
            int item=*reinterpret_cast<int*>(ui+0xb4+t*0x54+s*4);
            if(item>=-1 && item<21)layout[t][s]=item;
        }
    }
    if(slot.index>=counts[slot.tray])return false;
    int item=layout[slot.tray][slot.index];if(item<0 || item>=21)return false;
    int spell=talisman_spells[item][slot.tray],matches=0;
    // Confirm the slot is still equipped. Empty slots retain their config only.
    bool equipped_now=false;for(int i=0;i<n;i++)if(equipped[i]==spell)equipped_now=true;
    if(!equipped_now)return false;
    for(int i=0;i<count;i++){
        auto* icon=box+0xfc+i*0xc6;
        if(*reinterpret_cast<int*>(icon+0xb9)!=0 || *reinterpret_cast<int*>(icon+0xb5)!=spell)continue;
        if(*reinterpret_cast<int*>(icon+0x3d)==2)continue;
        *rect=*reinterpret_cast<RECT*>(icon+0x11);if(icon_index)*icon_index=i;matches++;
    }
    return matches==1;
}
int __cdecl battle_key(unsigned key,unsigned lparam){
    int k=key_index(key);
    if(k<0 || *reinterpret_cast<int*>(0x6e1f0c)>1 || !load() || !valid(bindings[k]))return 0;
    if((GetKeyState(VK_CONTROL)|GetKeyState(VK_MENU)|GetKeyState(VK_SHIFT))&0x8000)return 0;
    if(!*reinterpret_cast<void**>(0x6a2dd0+0x18ec))return 0;
    if(lparam&(1u<<30))return 1;
    RECT r{};int icon=-1;
    if(battle_rect(bindings[k],&r,&icon)){
        // Native spell-icon mouse-down sound (0x4d3f1c), same arguments.
        auto* control=reinterpret_cast<unsigned char*>(0x6a2dd0+0xfc+icon*0xc6);
        int sound=*reinterpret_cast<int*>(control+0x51);
        __asm {
            push -1
            push -1
            push 0
            push 0
            push 0
            push 0
            push sound
            mov ecx,6b0198h
            mov eax,56f000h
            call eax
        }
        // Exact native button callback: thiscall spellbox + icon index.
        typedef int (__thiscall* ClickFn)(void*,int);
        ((ClickFn)0x4d4d60)(reinterpret_cast<void*>(0x6a2dd0),icon);
    }
    return 1;
}
// The native click path clears every selected unit in 0x509bd0 even though
// target mode retains the wizard pointer. Bypass only that deselection loop;
// the function still sets target state and the pending spell normally.
unsigned preserve_selection_resume=0x509d47,selection_native=0x509cab,selection_next=0x509d29;
__declspec(naked) void preserve_selection_hook(){__asm{
    cmp dword ptr ds:[6e1f0ch],1
    jg native_path
    mov ecx,[esp+14h]
    jmp dword ptr [preserve_selection_resume]
native_path:
    cmp [esi+4],edi
    je next_unit
    jmp dword ptr [selection_native]
next_unit:
    jmp dword ptr [selection_next]
}}
// Only the battle viewport's native target-mode branch is remapped.
// Native 0x4fdc0c submits on right-down; its old left-down path changes
// selection. Cancel directly through pending-spell reset instead.
unsigned world_resume=0x4fdad6;
int __cdecl target_mouse(unsigned* flags){
    if(*reinterpret_cast<int*>(0x6e1f0c)>1 ||
       *reinterpret_cast<int*>(0x6903e8)!=2)return 0;
    auto* unit=*reinterpret_cast<unsigned char**>(0x6a2dd0+0x18ec);
    if(!readable(unit,0x5ec) || *reinterpret_cast<int*>(unit+0x5e8)<0)return 0;
    if(*flags&4){
        typedef void (__thiscall* PendingFn)(void*,int);
        ((PendingFn)0x509bd0)(unit,-1);
        return 1;
    }
    unsigned original=*flags;
    // Submit on release only. Down is reserved for the native drag anchor.
    *flags=(original&~15u)|((original&2u)<<1);
    return 0;
}
void __cdecl cancel_for_box_selection(){
    if(*reinterpret_cast<int*>(0x6e1f0c)>1 ||
       *reinterpret_cast<int*>(0x6903e8)!=2)return;
    auto* unit=*reinterpret_cast<unsigned char**>(0x6a2dd0+0x18ec);
    if(!readable(unit,0x5ec) || *reinterpret_cast<int*>(unit+0x5e8)<0)return;
    typedef void (__thiscall* PendingFn)(void*,int);
    ((PendingFn)0x509bd0)(unit,-1);
}
// Called only after the native >32-pixel drag threshold is crossed.
// Return the original selected-unit pointer to continue native box selection.
__declspec(naked) void box_selection_hook(){__asm{
    pushfd
    pushad
    call cancel_for_box_selection
    popad
    popfd
    mov eax,dword ptr ds:[6e9848h]
    ret
}}
__declspec(naked) void world_mouse_hook(){__asm{
    pushfd
    pushad
    lea eax,[esp+28h]
    push eax
    call target_mouse
    add esp,4
    test eax,eax
    jnz cancelled
    popad
    popfd
    sub esp,130h
    jmp dword ptr [world_resume]
cancelled:
    popad
    popfd
    xor eax,eax
    ret 2ch
}}
unsigned battle_resume=0x46c19a,battle_consumed=0x46e086;
__declspec(naked) void battle_key_hook(){__asm{
    pushfd
    pushad
    mov eax,[esp+58h]
    push eax
    push esi
    call battle_key
    add esp,8
    test eax,eax
    jnz consumed
    popad
    popfd
    lea edi,[eax-1]
    cmp edi,57h
    jmp dword ptr [battle_resume]
consumed:
    popad
    popfd
    jmp dword ptr [battle_consumed]
}}
void __cdecl labels(void* source) {
    if(source!=reinterpret_cast<void*>(0x6a49e0) || overlay_busy || !load())return;
    bool battle=*reinterpret_cast<void**>(0x6a2dd0+0x18ec)!=nullptr;
    if(!battle && !port_ui)return;
    auto* ui=static_cast<unsigned char*>(port_ui);
    if((!battle && *reinterpret_cast<int*>(ui+0x3e)) || *reinterpret_cast<int*>(0x6e1f0c)>1)return;
    int width=*reinterpret_cast<int*>(0x6a49f0),height=*reinterpret_cast<int*>(0x6a49f4);
    if(width!=1120 || height!=840)return;
    overlay_busy=true;
    typedef unsigned char* (__thiscall* LockFn)(void*);
    unsigned char* pixels=((LockFn)0x58b660)(source);
    if(pixels){
        int pitch=*reinterpret_cast<int*>(0x6a49f8);
        if(pitch>=width*2 && pitch<=16384){
            for(int k=0;k<12;k++)if(valid(bindings[k])){
                Slot slot=bindings[k];RECT target{};
                if(battle){if(!battle_rect(slot,&target))continue;}
                else{
                    int count=*reinterpret_cast<int*>(ui+0x84+4*slot.tray);
                    if(slot.index>=count || count>21)continue;
                    auto* controls=*reinterpret_cast<unsigned char**>(ui+0x218+4*slot.tray);
                    if(!readable(controls,count*0x86))continue;
                    target=*reinterpret_cast<RECT*>(controls+slot.index*0x86+0x11);
                }
                auto* r=&target;
                int x=r->right-18,y=r->bottom-23;
                if(x<0 || y<0 || x+14>=width || y+18>=height)continue;
                for(int yy=0;yy<18;yy++)for(int xx=0;xx<14;xx++){
                    unsigned short colour=(xx==0 || yy==0 || xx==13 || yy==17)?0xffff:0;
                    if(xx>=2 && xx<12 && yy>=2 && yy<16 &&
                       (glyphs[k][(yy-2)/2] & (1<<(4-(xx-2)/2))))colour=0xffe0;
                    *reinterpret_cast<unsigned short*>(pixels+(y+yy)*pitch+(x+xx)*2)=colour;
                }
            }
        }
        void* surface=*reinterpret_cast<void**>(0x6a49e4);
        typedef HRESULT (__stdcall* UnlockFn)(void*,void*);
        ((UnlockFn)(*reinterpret_cast<void***>(surface))[0x80/4])(surface,pixels);
    }
    overlay_busy=false;
}
__declspec(naked) void present_hook(){__asm{
    pushfd
    pushad
    push ecx
    call labels
    add esp,4
    popad
    popfd
    sub esp,30h
    push ebx
    push ebp
    push esi
    jmp dword ptr [present_resume]
}}
bool install() {
    constexpr unsigned char battle_original[]={0x8d,0x78,0xff,0x83,0xff,0x57};
    if(memcmp(reinterpret_cast<void*>(0x46c194),battle_original,6))return false;
    if(memcmp(reinterpret_cast<void*>(kHandler),kOriginal,sizeof(kOriginal)))return false;
    constexpr unsigned char selection_original[]={0x39,0x7e,0x04,0x74,0x7e};
    constexpr unsigned char mouse_original[]={0x81,0xec,0x30,0x01,0x00,0x00};
    constexpr unsigned char sound_original[]={0x53,0x55,0x8b,0xe9,0x56,0x57};
    constexpr unsigned char drag_original[]={0xe8,0xcc,0x20,0x06,0x00};
    if(memcmp(reinterpret_cast<void*>(0x509ca6),selection_original,5) ||
       memcmp(reinterpret_cast<void*>(0x4fdad0),mouse_original,6) ||
       memcmp(reinterpret_cast<void*>(0x56f000),sound_original,6))return false;
    if(memcmp(reinterpret_cast<void*>(0x4a54cf),drag_original,5))return false;
    DWORD old=0;
    if(!VirtualProtect(reinterpret_cast<void*>(kHandler),sizeof(kOriginal),PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char patch[sizeof(kOriginal)]={0xe9,0,0,0,0,0x90,0x90};
    *reinterpret_cast<int*>(patch+1)=static_cast<int>(reinterpret_cast<uintptr_t>(handler_hook)-kHandler-5);
    memcpy(reinterpret_cast<void*>(kHandler),patch,sizeof(patch));
    FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(kHandler),sizeof(patch));
    DWORD unused=0;VirtualProtect(reinterpret_cast<void*>(kHandler),sizeof(patch),old,&unused);
    constexpr unsigned char present_original[]={0x83,0xec,0x30,0x53,0x55,0x56};
    void* site=reinterpret_cast<void*>(0x58bf40);
    if(memcmp(site,present_original,6))return false;
    if(!VirtualProtect(site,6,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char draw_patch[]={0xe9,0,0,0,0,0x90};
    *reinterpret_cast<int*>(draw_patch+1)=static_cast<int>(reinterpret_cast<uintptr_t>(present_hook)-0x58bf40-5);
    memcpy(site,draw_patch,6);FlushInstructionCache(GetCurrentProcess(),site,6);
    VirtualProtect(site,6,old,&unused);
    site=reinterpret_cast<void*>(0x46c194);
    if(!VirtualProtect(site,6,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char key_patch[]={0xe9,0,0,0,0,0x90};
    *reinterpret_cast<int*>(key_patch+1)=static_cast<int>(reinterpret_cast<uintptr_t>(battle_key_hook)-0x46c194-5);
    memcpy(site,key_patch,6);FlushInstructionCache(GetCurrentProcess(),site,6);
    VirtualProtect(site,6,old,&unused);
    site=reinterpret_cast<void*>(0x509ca6);
    if(!VirtualProtect(site,5,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char selection_patch[]={0xe9,0,0,0,0};
    *reinterpret_cast<int*>(selection_patch+1)=static_cast<int>(reinterpret_cast<uintptr_t>(preserve_selection_hook)-0x509ca6-5);
    memcpy(site,selection_patch,5);FlushInstructionCache(GetCurrentProcess(),site,5);
    VirtualProtect(site,5,old,&unused);
    site=reinterpret_cast<void*>(0x4fdad0);
    if(!VirtualProtect(site,6,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char mouse_patch[]={0xe9,0,0,0,0,0x90};
    *reinterpret_cast<int*>(mouse_patch+1)=static_cast<int>(reinterpret_cast<uintptr_t>(world_mouse_hook)-0x4fdad0-5);
    memcpy(site,mouse_patch,6);FlushInstructionCache(GetCurrentProcess(),site,6);
    VirtualProtect(site,6,old,&unused);
    site=reinterpret_cast<void*>(0x4a54cf);
    if(!VirtualProtect(site,5,PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char drag_patch[]={0xe8,0,0,0,0};
    *reinterpret_cast<int*>(drag_patch+1)=static_cast<int>(reinterpret_cast<uintptr_t>(box_selection_hook)-0x4a54cf-5);
    memcpy(site,drag_patch,5);FlushInstructionCache(GetCurrentProcess(),site,5);
    VirtualProtect(site,5,old,&unused);
    return true;
}
}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID) {
    if(reason==DLL_PROCESS_ATTACH){
        DisableThreadLibraryCalls(instance);
        if(*reinterpret_cast<int*>(0x6e1f0c)>1)return FALSE;
        return install()?TRUE:FALSE;
    }
    return TRUE;
}
