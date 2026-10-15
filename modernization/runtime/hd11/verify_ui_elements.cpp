#include "ui_geometry.h"
#include <cstdio>
#include <cstdlib>
static int checks;
static void check(bool b){++checks;if(!b){std::fprintf(stderr,"UI element case %d failed\n",checks);std::exit(1);}}
int main(){
 auto v=mm_ui_fit(2560,1440);
 for(int frame=0;frame<234;frame++){
  check(mm_ui_port_icon(1,1,v,2,1292,52,1386,156,frame));
  check(!mm_ui_port_icon(0,1,v,1,646,26,693,78,frame));
  check(!mm_ui_port_icon(1,0,v,2,1292,52,1386,156,frame));
 }
 check(!mm_ui_port_icon(1,1,v,2,1292,52,1386,156,234));
 check(!mm_ui_port_icon(1,1,v,2,1292,52,1386,156,-1));
 check(!mm_ui_port_icon(1,1,v,2,1292,52,1332,92,54));
 check(!mm_ui_port_icon(1,1,v,2,100,52,194,156,54));
 check(mm_ui_clamp_origin(147,600,v.x,v.x+v.width)==320);
 check(mm_ui_clamp_origin(2180,600,v.x,v.x+v.width)==1640);
 check(mm_ui_clamp_origin(600,600,v.x,v.x+v.width)==600);
 check(mm_ui_clamp_origin(1400,106,0,1440)==1334);
 check(mm_ui_clamp_origin(-10,106,0,1440)==0);
 for(int width=600;width<=1920;width+=60)for(int origin=-300;origin<=2600;origin+=37){
  int x=mm_ui_clamp_origin(origin,width,v.x,v.x+v.width);
  check(x>=v.x && x+width<=v.x+v.width);
 }
 std::printf("%d UI frame-policy/tooltip bounds checks passed\n",checks);
}
