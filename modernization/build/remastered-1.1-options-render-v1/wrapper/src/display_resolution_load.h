#ifndef MM_DISPLAY_RESOLUTION_H
#define MM_DISPLAY_RESOLUTION_H
#include <windows.h>
#include <string.h>
static int mm_display_width(void){
    char value[32]={0};
    GetPrivateProfileStringA("display","resolution","",value,sizeof value,".\\remastered-settings.ini");
    return !strcmp(value,"1920x1080")?1920:!strcmp(value,"2560x1440")?2560:0;
}
static void mm_display_load_window_mode(void){
    char value[32]={0};
    GetPrivateProfileStringA("display","window_mode","windowed",value,sizeof value,".\\remastered-settings.ini");
    if(!strcmp(value,"windowed") || !strcmp(value,"borderless")){
        g_config.windowed=TRUE;
        g_config.fullscreen=FALSE;
        g_config.border=strcmp(value,"borderless")!=0;
    }
}
static void mm_display_load_resolution(void){
    int width=mm_display_width();
    if(width){
        g_config.window_rect.right=width;
        g_config.window_rect.bottom=width*9/16;
        g_config.fullscreen=FALSE;
    }
    mm_display_load_window_mode();
}

#endif
