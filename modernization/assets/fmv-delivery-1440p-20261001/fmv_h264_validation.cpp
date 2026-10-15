// Isolated opt-in FMV bridge. Disk engine unchanged; missing MP4 uses native AVI.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mfplay.h>
#include <mfapi.h>
#include <propvarutil.h>
#include <bcrypt.h>
#include <string>
#include <vector>
#include <atomic>
#include <cstdio>
#include <cstdint>
#include <cstring>
#pragma comment(lib,"mfplay.lib")
#pragma comment(lib,"mfplat.lib")
#pragma comment(lib,"mfuuid.lib")
#pragma comment(lib,"ole32.lib")
#pragma comment(lib,"bcrypt.lib")
static HINSTANCE module;
static void log(const char* event,long value=0){
 HANDLE f=CreateFileW(L"fmv-h264-events.jsonl",FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(f==INVALID_HANDLE_VALUE)return;
 char line[256];int n=sprintf_s(line,"{\"event\":\"%s\",\"value\":%ld,\"tick_ms\":%llu}\n",event,value,GetTickCount64());DWORD written;
 WriteFile(f,line,n,&written,nullptr);CloseHandle(f);
}
struct Callback:IMFPMediaPlayerCallback {
 std::atomic<ULONG> refs{1};std::atomic<bool> done{false},playing{false};std::atomic<long> error{0};
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID id,void** out)override{if(!out)return E_POINTER;*out=nullptr;if(id==__uuidof(IUnknown)||id==__uuidof(IMFPMediaPlayerCallback)){*out=this;AddRef();return S_OK;}return E_NOINTERFACE;}
 ULONG STDMETHODCALLTYPE AddRef()override{return ++refs;}
 ULONG STDMETHODCALLTYPE Release()override{ULONG r=--refs;if(!r)delete this;return r;}
 void STDMETHODCALLTYPE OnMediaPlayerEvent(MFP_EVENT_HEADER* e)override{
  if(FAILED(e->hrEvent)){error=e->hrEvent;done=true;log("mf_error",e->hrEvent);return;}
  HRESULT hr=S_OK;
  if(e->eEventType==MFP_EVENT_TYPE_MEDIAITEM_CREATED){auto x=MFP_GET_MEDIAITEM_CREATED_EVENT(e);BOOL has=FALSE,selected=FALSE;if(SUCCEEDED(x->pMediaItem->HasAudio(&has,&selected))){log("has_audio",has);log("audio_selected",selected);}hr=e->pMediaPlayer->SetMediaItem(x->pMediaItem);}
  else if(e->eEventType==MFP_EVENT_TYPE_MEDIAITEM_SET){SIZE n{},a{};hr=e->pMediaPlayer->GetNativeVideoSize(&n,&a);log("video_width",n.cx);log("video_height",n.cy);if(SUCCEEDED(hr))hr=e->pMediaPlayer->Play();}
  else if(e->eEventType==MFP_EVENT_TYPE_PLAY){playing=true;log("play");}
  else if(e->eEventType==MFP_EVENT_TYPE_PLAYBACK_ENDED){done=true;log("ended");}
  if(FAILED(hr)){error=hr;done=true;log("mf_command_error",hr);}
 }
};
struct View{IMFPMediaPlayer* player=nullptr;bool skip=false;};
static LRESULT CALLBACK wndproc(HWND h,UINT m,WPARAM w,LPARAM l){
 auto v=(View*)GetWindowLongPtrW(h,GWLP_USERDATA);
 if(m==WM_NCCREATE){v=(View*)((CREATESTRUCTW*)l)->lpCreateParams;SetWindowLongPtrW(h,GWLP_USERDATA,(LONG_PTR)v);}
 if(v && ((m==WM_KEYDOWN && (w==VK_ESCAPE || w==VK_SPACE || w==VK_RETURN)) || m==WM_LBUTTONDOWN || m==WM_RBUTTONDOWN)){log("skip_window_message",m);v->skip=true;return 0;}
 if(m==WM_ERASEBKGND)return 1;
 if(m==WM_PAINT){PAINTSTRUCT p;BeginPaint(h,&p);if(v&&v->player)v->player->UpdateVideo();else FillRect(p.hdc,&p.rcPaint,(HBRUSH)GetStockObject(BLACK_BRUSH));EndPaint(h,&p);return 0;}
 if(m==WM_SIZE && v && v->player)v->player->UpdateVideo();
 return DefWindowProcW(h,m,w,l);
}
static BOOL CALLBACK find_window(HWND h,LPARAM p){DWORD pid;GetWindowThreadProcessId(h,&pid);if(pid==GetCurrentProcessId() && IsWindowVisible(h) && !GetWindow(h,GW_OWNER)){*(HWND*)p=h;return FALSE;}return TRUE;}
// Returns -1 on decoder failure (native fallback), 0 on skip, 1 on completion.
extern "C" __declspec(dllexport) int __cdecl mm_fmv_play(HWND parent,const wchar_t* path){
 if(!IsWindow(parent))return -1;
 HRESULT ci=CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED);if(FAILED(ci)&&ci!=RPC_E_CHANGED_MODE)return -1;
 WNDCLASSW wc{};wc.hInstance=module;wc.lpfnWndProc=wndproc;wc.lpszClassName=L"MagicMayhem.H264.FMV.v1";wc.hbrBackground=(HBRUSH)GetStockObject(BLACK_BRUSH);RegisterClassW(&wc);
 RECT r;GetClientRect(parent,&r);View view;
 HWND focus=GetFocus();HWND child=CreateWindowExW(0,wc.lpszClassName,L"FMV",WS_CHILD|WS_VISIBLE|WS_CLIPSIBLINGS,0,0,r.right,r.bottom,parent,nullptr,module,&view);
 if(!child){if(SUCCEEDED(ci))CoUninitialize();return -1;}
 SetWindowPos(child,HWND_TOP,0,0,r.right,r.bottom,SWP_SHOWWINDOW);SetFocus(child);
 log("client_width",r.right);log("client_height",r.bottom);
 auto cb=new Callback;
 HRESULT hr=MFPCreateMediaPlayer(nullptr,FALSE,MFP_OPTION_FREE_THREADED_CALLBACK,cb,child,&view.player);
 if(SUCCEEDED(hr))view.player->SetVolume(0.0f);
 if(SUCCEEDED(hr))hr=view.player->CreateMediaItemFromURL(path,FALSE,0,nullptr);
 ULONGLONG start=GetTickCount64();bool quit=false;int quitcode=0;
 while(SUCCEEDED(hr)&&!cb->done&&!view.skip&&IsWindow(parent)){
  MSG msg;while(PeekMessageW(&msg,nullptr,0,0,PM_REMOVE)){
   if(msg.message==WM_QUIT){quit=true;quitcode=(int)msg.wParam;view.skip=true;break;}
   if(msg.message==WM_CLOSE && msg.hwnd==parent){quit=true;view.skip=true;quitcode=0;break;}
   if(((msg.message==WM_KEYDOWN&&(msg.wParam==VK_ESCAPE||msg.wParam==VK_SPACE||msg.wParam==VK_RETURN))||msg.message==WM_LBUTTONDOWN||msg.message==WM_RBUTTONDOWN)&&GetTickCount64()-start>300){log("skip_message",msg.message);log("skip_key",(long)msg.wParam);view.skip=true;break;}
   TranslateMessage(&msg);DispatchMessageW(&msg);
  }
  RECT nr;GetClientRect(parent,&nr);if(nr.right!=r.right||nr.bottom!=r.bottom){r=nr;SetWindowPos(child,HWND_TOP,0,0,r.right,r.bottom,SWP_NOACTIVATE);}
  if(!cb->playing&&GetTickCount64()-start>30000){hr=HRESULT_FROM_WIN32(WAIT_TIMEOUT);break;}
  if(GetTickCount64()-start>180000){hr=HRESULT_FROM_WIN32(WAIT_TIMEOUT);break;}
  MsgWaitForMultipleObjects(0,nullptr,FALSE,15,QS_ALLINPUT);
 }
 bool failure=FAILED(hr)||cb->error!=0;
 if(view.player){view.player->Shutdown();view.player->Release();view.player=nullptr;}
 int result=failure?-1:view.skip?0:1;cb->Release();DestroyWindow(child);if(IsWindow(focus))SetFocus(focus);
 if(quit)PostQuitMessage(quitcode);if(SUCCEEDED(ci))CoUninitialize();log("return",result);return result;
}
using Native=int(__fastcall*)(const char*,void*,void*,int,int,int);
static Native native=nullptr;
static int __fastcall movie(const char* filename,void* edx,void* surface,int x,int y,int mode){
 std::string text=filename?filename:"";auto dot=text.find_last_of('.');if(dot!=std::string::npos)text.replace(dot,std::string::npos,".mp4");
 wchar_t path[32768];int n=MultiByteToWideChar(CP_ACP,0,text.c_str(),-1,path,32768);
 if(n>0 && GetFileAttributesW(path)!=INVALID_FILE_ATTRIBUTES){
  HWND window=nullptr;EnumWindows(find_window,(LPARAM)&window);log("hook_enter");
  int answer=mm_fmv_play(window,path);if(answer>=0)return answer;log("fallback_avi");
 }
 return native(filename,edx,surface,x,y,mode);
}
// Launcher already hashes the unchanged engine; independently require exact
// original prologue and fixed preferred base before this isolated detour.
extern "C" __declspec(dllexport) BOOL __cdecl mm_fmv_install(){
 if(native)return TRUE;if(GetModuleHandleW(nullptr)!=(HMODULE)0x400000)return FALSE;
 unsigned char expected[]={0x51,0x8d,0x44,0x24,0x00,0x56};BYTE* site=(BYTE*)0x469a00;
 if(memcmp(site,expected,6))return FALSE;
 BYTE* t=(BYTE*)VirtualAlloc(nullptr,11,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);if(!t)return FALSE;
 memcpy(t,site,6);t[6]=0xe9;*(int32_t*)(t+7)=(int32_t)((uintptr_t)(site+6)-(uintptr_t)(t+11));native=(Native)t;
 DWORD old; if(!VirtualProtect(site,6,PAGE_EXECUTE_READWRITE,&old))return FALSE;
 site[0]=0xe9;*(int32_t*)(site+1)=(int32_t)((uintptr_t)movie-(uintptr_t)(site+5));site[5]=0x90;
 FlushInstructionCache(GetCurrentProcess(),site,6);DWORD ignored;VirtualProtect(site,6,old,&ignored);log("installed");return TRUE;
}
BOOL WINAPI DllMain(HINSTANCE h,DWORD reason,LPVOID){if(reason==DLL_PROCESS_ATTACH){module=h;DisableThreadLibraryCalls(h);wchar_t flag[8];if(GetEnvironmentVariableW(L"MM_FMV_H264",flag,8)&&flag[0]==L'1')return mm_fmv_install();}return TRUE;}
