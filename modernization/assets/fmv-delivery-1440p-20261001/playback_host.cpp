// Exercise the exact production player export without starting/contending with a game.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
static LRESULT CALLBACK window_proc(HWND h,UINT m,WPARAM w,LPARAM l){return DefWindowProcW(h,m,w,l);}
int wmain(int argc,wchar_t** argv){
 if(argc!=3)return 2;SetEnvironmentVariableW(L"MM_FMV_H264",L"0");SetEnvironmentVariableW(L"MM_FMV_DIAG_MUTED",L"1");
 HMODULE dll=LoadLibraryW(argv[1]);if(!dll)return 3;
 auto play=(int(__cdecl*)(HWND,const wchar_t*))GetProcAddress(dll,"mm_fmv_play");if(!play)return 4;
 WNDCLASSW c{};c.hInstance=GetModuleHandleW(nullptr);c.lpfnWndProc=window_proc;c.lpszClassName=L"MagicMayhem.FMV.HiddenValidation";RegisterClassW(&c);
 HWND h=CreateWindowW(c.lpszClassName,L"FMV hidden validation",WS_POPUP,0,0,2560,1440,nullptr,nullptr,c.hInstance,nullptr);if(!h)return 5;
 // Window intentionally remains hidden; no foreground/cursor input or game names.
 ULONGLONG started=GetTickCount64();int result=play(h,argv[2]);printf("{\"return\":%d,\"elapsed_ms\":%llu,\"hidden\":true,\"muted_for_shared_desktop\":true}\n",result,GetTickCount64()-started);DestroyWindow(h);FreeLibrary(dll);return result==1?0:6;
}
