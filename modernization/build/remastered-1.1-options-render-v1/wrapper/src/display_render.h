#ifndef MM_DISPLAY_RENDER_H
#define MM_DISPLAY_RENDER_H
#include <windows.h>
static void mm_display_load_render(void){
 int fps=GetPrivateProfileIntA("display","render_fps",60,".\\remastered-settings.ini");
 if(fps!=60 && fps!=120)fps=60;
 g_config.maxfps=fps;g_config.minfps=-1;g_config.vsync=FALSE;
}
static UINT mm_display_render_message(void){return RegisterWindowMessageA("MagicMayhem.Remastered.Render.v1");}
static LRESULT mm_display_apply_render(WPARAM fps,LPARAM unused){
 if((fps!=60 && fps!=120)||unused)return FALSE;
 g_config.maxfps=(int)fps;g_config.minfps=-1;g_config.vsync=FALSE;
 return SUCCEEDED(dd_SetDisplayMode(0,0,0,0));
}
#endif
