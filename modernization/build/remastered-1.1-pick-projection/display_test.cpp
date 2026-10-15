
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cassert>
#include <cstdio>
#include <initializer_list>
struct Config {RECT window_rect;BOOL fullscreen;} g_config;
static int resets;
static HRESULT dd_SetDisplayMode(DWORD w,DWORD h,DWORD b,DWORD f){assert(!w&&!h&&!b&&!f);++resets;return S_OK;}
#include "display_resolution.h"
int main(){
 const char* path=".\\remastered-settings.ini";
 DeleteFileA(path);
 assert(mm_display_width()==0);
 for(int w: {1920,2560}){
  WritePrivateProfileStringA("display","resolution",w==1920?"1920x1080":"2560x1440",path);
  assert(mm_display_width()==w);g_config.fullscreen=TRUE;mm_display_load_resolution();
  assert(g_config.window_rect.right==w && g_config.window_rect.bottom==w*9/16 && !g_config.fullscreen);
  assert(mm_display_apply_resolution(w,w*9/16));
 }
 assert(resets==2);assert(!mm_display_apply_resolution(800,600));assert(!mm_display_apply_resolution(1920,1440));
 WritePrivateProfileStringA("display","resolution","corrupt",path);assert(!mm_display_width());
 DeleteFileA(path);puts("Native persistence/load/live reset validation passed");
}
