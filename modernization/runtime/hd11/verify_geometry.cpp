#include "ui_geometry.h"
#include <cstdio>
#include <cstdlib>
#include <initializer_list>
static int checks=0;
static void check(bool b){++checks;if(!b){std::fprintf(stderr,"geometry case %d failed\n",checks);std::exit(1);}}
int main(){
 for(auto wh : {1280,1920,2560,3840}){
  int height=wh*9/16;auto v=mm_ui_fit(wh,height);
  check(v.width==height*4/3);check(v.x==(wh-v.width)/2);check(v.y==0);
  check(mm_ui_project_x(v,0)==v.x);check(mm_ui_project_y(v,0)==0);
  check(mm_ui_project_x(v,800)==v.x+v.width);check(mm_ui_project_y(v,600)==height);
  int rx,ry;check(!mm_ui_inverse(v,v.x-1,0,&rx,&ry));check(!mm_ui_inverse(v,v.x+v.width,0,&rx,&ry));
  check(!mm_ui_inverse(v,v.x,height,&rx,&ry));
  for(int y=0;y<600;y+=17)for(int x=0;x<800;x+=19){
   int px=mm_ui_project_x(v,x),py=mm_ui_project_y(v,y);
   check(mm_ui_inverse(v,px,py,&rx,&ry));check(abs(rx-x)<=1 && abs(ry-y)<=1);
  }
 }
 auto v=mm_ui_fit(2560,1440);check(v.x==320 && v.width==1920 && v.height==1440);
 check(mm_ui_project_x(v,100)==560 && mm_ui_project_y(v,100)==240);
 v=mm_ui_fit(1280,720);check(v.x==160 && mm_ui_project_x(v,100)==280 && mm_ui_project_y(v,100)==120);
 v=mm_ui_fit(0,0);int x,y;check(!mm_ui_inverse(v,0,0,&x,&y));
 std::printf("%d geometry checks passed (1K/1080p/2K/4K math only)\n",checks);
}
