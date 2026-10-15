static unsigned char* fixture_table[3];
static int fixture_count;
#define MM_HD_CONTROL_TABLE ((uintptr_t)fixture_table)
#define MM_HD_CONTROL_COUNT ((uintptr_t)&fixture_count)
#include "layout_context.h"
#include <cstdio>
#include <cstdlib>
static int checks;
static void check(bool value){if(!value){std::fprintf(stderr,"layout check %d failed\n",checks+1);std::exit(1);}checks++;}
int main(){
    unsigned char controls[3][0x40]={};
    auto** table=fixture_table;auto* count=&fixture_count;
    *count=0;check(mm_hd_current().mode==MM_HD_UI);
    *(DWORD*)controls[0]=0x5c6ee8;*(DWORD*)controls[1]=0x5c6f54;
    int rect[]={0,0,1280,720};memcpy(controls[0]+0x11,rect,sizeof(rect));memcpy(controls[1]+0x11,rect,sizeof(rect));
    table[0]=controls[0];table[1]=controls[1];*count=2;
    MmHdLayoutContext battle=mm_hd_current();check(battle.mode==MM_HD_BATTLE);
    check(battle.content_width==1280 && battle.content_height==720 && battle.output_scale==2 && battle.font_scale==1);
    POINT input=mm_hd_input(battle,2500,1400);check(input.x==1250 && input.y==700);
    input=mm_hd_input(battle,2559,1439);check(input.x==1279 && input.y==719);
    input=mm_hd_input(battle,0,0);check(input.x==0 && input.y==0);
    // Save/load and independent pages may coexist with stale world pointers.
    table[2]=controls[2];*count=3;rect[2]=2240;rect[3]=1440;memcpy(controls[2]+0x11,rect,sizeof(rect));
    MmHdLayoutContext ui=mm_hd_current();check(ui.mode==MM_HD_UI);
    check(ui.content_x==320 && ui.content_width==1920 && ui.content_height==1440 && ui.output_scale==1 && ui.font_scale==2);
    input=mm_hd_input(ui,320,0);check(input.x==320 && input.y==0);
    input=mm_hd_input(ui,2239,1439);check(input.x==2239 && input.y==1439);
    *count=2;check(mm_hd_current().mode==MM_HD_BATTLE);
    table[1]=(unsigned char*)1;check(mm_hd_current().mode==MM_HD_UI);
    *count=401;check(mm_hd_current().mode==MM_HD_UI);
    *count=-1;check(mm_hd_current().mode==MM_HD_UI);
    std::printf("%d layout/transition/input checks passed; no game process\n",checks);
    return 0;
}
