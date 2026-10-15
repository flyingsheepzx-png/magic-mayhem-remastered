// Isolated single-player Portmanteau binding trial. No casting path is changed.
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
    HWND hwnd=*reinterpret_cast<HWND*>(0x656614);
    POINT point{};RECT client{};
    if(!hwnd || !GetCursorPos(&point) || !ScreenToClient(hwnd,&point) ||
       !GetClientRect(hwnd,&client))return false;
    int width=*reinterpret_cast<int*>(0x6a49f0),height=*reinterpret_cast<int*>(0x6a49f4);
    if(width<800 || width>1120 || height<600 || height>840 ||
       client.right<=0 || client.bottom<=0 || point.x<0 || point.y<0 ||
       point.x>=client.right || point.y>=client.bottom)return false;
    POINT native{point.x*width/client.right,point.y*height/client.bottom};
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
bool install() {
    if(memcmp(reinterpret_cast<void*>(kHandler),kOriginal,sizeof(kOriginal)))return false;
    DWORD old=0;
    if(!VirtualProtect(reinterpret_cast<void*>(kHandler),sizeof(kOriginal),PAGE_EXECUTE_READWRITE,&old))return false;
    unsigned char patch[sizeof(kOriginal)]={0xe9,0,0,0,0,0x90,0x90};
    *reinterpret_cast<int*>(patch+1)=static_cast<int>(reinterpret_cast<uintptr_t>(handler_hook)-kHandler-5);
    memcpy(reinterpret_cast<void*>(kHandler),patch,sizeof(patch));
    FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(kHandler),sizeof(patch));
    DWORD unused=0;VirtualProtect(reinterpret_cast<void*>(kHandler),sizeof(patch),old,&unused);
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
