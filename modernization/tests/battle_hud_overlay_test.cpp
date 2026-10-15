#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <vector>
#include <cstdio>
#include <cstring>
#include <chrono>
#include <cassert>
static int control_count;
static unsigned char* control_table[400];
#define MM_HD_CONTROL_COUNT ((uintptr_t)&control_count)
#define MM_HD_CONTROL_TABLE ((uintptr_t)control_table)
#include "layout_context.h"
typedef struct IDirectDrawSurfaceImpl {void* surface;int pitch;} IDirectDrawSurfaceImpl;
#include "mm_battle_hud.h"
int main(int argc,char**){
 mm_hud_load();assert(mm_hud_count>0);
 const int pitch=5120;
 std::vector<unsigned char> src(pitch*1440,0x36),dst(pitch*1440,0x27),before;
 IDirectDrawSurfaceImpl primary={src.data(),pitch};unsigned char control[256]{};
 if(argc>1){
  FILE* f=fopen("scene.bin","rb");assert(f);assert(fread(src.data(),1,src.size(),f)==src.size());fclose(f);
  f=fopen("controls.bin","rb");assert(f);assert(fread(&control_count,4,1,f)==1);assert(control_count>0&&control_count<=400);
  std::vector<std::vector<unsigned char>> controls(control_count,std::vector<unsigned char>(256));
  for(int i=0;i<control_count;i++){unsigned row[5];assert(fread(row,4,5,f)==5);*(unsigned*)controls[i].data()=row[0];memcpy(controls[i].data()+0x11,row+1,16);control_table[i]=controls[i].data();}fclose(f);
  for(int y=0;y<720;y++)for(int x=0;x<1280;x++){
   unsigned short c=((unsigned short*)(src.data()+y*pitch))[x];
   for(int dy=0;dy<2;dy++)for(int dx=0;dx<2;dx++)((unsigned short*)(dst.data()+(y*2+dy)*pitch))[x*2+dx]=c;
  }
  before=src;auto old=dst;auto start=std::chrono::steady_clock::now();mm_hud_present(&primary,dst.data());
  unsigned count=0,changed=0;
  for(int i=0;i<control_count;i++)if(mm_hud_cache[i].owner&&mm_hud_cache[i].tile>=0){count++;printf("control%d template%d at%d,%d dim%d\n",i,mm_hud_cache[i].tile,mm_hud_cache[i].x,mm_hud_cache[i].y,mm_hud_cache[i].dim);}
  for(size_t i=0;i<dst.size();i++)changed+=dst[i]!=old[i];assert(src==before);assert(count>=3&&changed>1000);
  printf("Real captured HUD: %u identified icons/portraits, %u changed bytes; %.3f ms; source unchanged\n",count,changed,std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count());
  start=std::chrono::steady_clock::now();for(int repeat=0;repeat<100;repeat++)mm_hud_present(&primary,dst.data());
  printf("Cached HUD overlay: %.3f ms/frame\n",std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()/100);
  f=fopen("output.bin","wb");assert(f);assert(fwrite(dst.data(),1,dst.size(),f)==dst.size());fclose(f);return 0;
 }
 control_count=1;control_table[0]=control;
 unsigned cases=0;double worst=0;
 for(unsigned n=0;n<mm_hud_count;n++)for(int dim=0;dim<3;dim++){
  const MmHudTile& t=mm_hud_tiles[n];const int x=100,y=400;
  std::fill(src.begin(),src.end(),0x36);std::fill(dst.begin(),dst.end(),0x27);
  mm_hud_cache[0].owner=NULL;
  *(unsigned*)control=t.kind==2?0x5c6e4c:0x5c6e38;
  int rect[4]={x,y,x+(int)t.w,y+(int)t.h};memcpy(control+0x11,rect,sizeof(rect));
  for(unsigned j=0;j<t.h;j++)for(unsigned i=0;i<t.w;i++)if(t.mask[j*t.w+i])
   ((unsigned short*)(src.data()+(y+j)*pitch))[x+i]=mm_hud_tint(t.low[j*t.w+i],dim);
  before=src;
  auto start=std::chrono::steady_clock::now();mm_hud_present(&primary,dst.data());
  double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();if(ms>worst)worst=ms;
  assert(before==src);assert(mm_hud_cache[0].tile>=0);
  // Exact output and original colour-key footprint; other scene/HUD unchanged.
  for(int j=0;j<1440;j++)for(int i=0;i<2560;i++){
   unsigned short expected=0x2727;
   if(i>=x*2 && i<(x+(int)t.w)*2 && j>=y*2 && j<(y+(int)t.h)*2){
    unsigned rx=i-x*2,ry=j-y*2,k=(ry/2)*t.w+rx/2;
    if(t.mask[k])expected=mm_hud_tint(t.high[ry*t.w*2+rx],dim);
   }
   // Identical templates can select an earlier variant; ensure its artwork
   // rather than uninitialized cache metadata supplies expected pixels.
   const MmHudTile& chosen=mm_hud_tiles[mm_hud_cache[0].tile];
   if(i>=x*2 && i<(x+(int)t.w)*2 && j>=y*2 && j<(y+(int)t.h)*2){
    unsigned rx=i-x*2,ry=j-y*2,k=(ry/2)*t.w+rx/2;
    if(t.mask[k] && chosen.w==t.w && chosen.h==t.h)expected=mm_hud_tint(chosen.high[ry*t.w*2+rx],mm_hud_cache[0].dim);
   }
   if(t.kind==3 && expected!=0x2727){
    // Multiple sheet halves may share identical neck/background rows. The
    // selected model row can differ there; coverage and scene bounds cannot.
    assert(((unsigned short*)(dst.data()+j*pitch))[i]!=0x2727);continue;
   }
   if(((unsigned short*)(dst.data()+j*pitch))[i]!=expected){printf("Mismatch tile%u kind%u dim%d chosen%d at%d,%d location%d,%d expected%x got%x\n",n,t.kind,dim,mm_hud_cache[0].tile,i,j,mm_hud_cache[0].x,mm_hud_cache[0].y,expected,((unsigned short*)(dst.data()+j*pitch))[i]);return 2;}
  }
  // Dynamic overlay pixel is preserved even if all identifying anchors match.
  unsigned k=0;while(k<t.w*t.h){bool anchor=false;for(int a=0;a<24;a++)if(t.anchors[a]==k)anchor=true;if(t.mask[k]&&!anchor)break;k++;}
  if(k<t.w*t.h){
   ((unsigned short*)(src.data()+(y+k/t.w)*pitch))[x+k%t.w]^=0xffff;
   std::fill(dst.begin(),dst.end(),0x27);mm_hud_present(&primary,dst.data());
   assert(((unsigned short*)(dst.data()+(y+k/t.w)*2*pitch))[(x+k%t.w)*2]==0x2727);
  }
  // Unrelated controls are never candidates.
  *(unsigned*)control=0x5c6a8c;std::fill(dst.begin(),dst.end(),0x27);mm_hud_present(&primary,dst.data());
  for(auto b:dst)assert(b==0x27);
  cases++;
 }
 FILE* pairs=fopen("healthpairs.bin","rb");assert(pairs);unsigned pair_count;assert(fread(&pair_count,4,1,pairs)==1);
 unsigned health_cases=0;
 for(unsigned pair=0;pair<pair_count;pair++){
  unsigned ids[2];assert(fread(ids,4,2,pairs)==2);assert(ids[0]<mm_hud_count&&ids[1]<mm_hud_count);
  const MmHudTile& alive=mm_hud_tiles[ids[0]];const MmHudTile& dead=mm_hud_tiles[ids[1]];assert(alive.kind==3&&dead.kind==3);
  for(int shift: {-1,0,1})for(unsigned split: {12u,32u,52u}){
   const int x=100,y=400;std::fill(src.begin(),src.end(),0x36);std::fill(dst.begin(),dst.end(),0x27);mm_hud_cache[0].owner=NULL;
   *(unsigned*)control=0x5c6e38;int rect[4]={x,y,x+(int)alive.w,y+(int)alive.h};memcpy(control+0x11,rect,16);
   for(unsigned j=0;j<alive.h;j++)for(unsigned i=0;i<alive.w;i++){
    const MmHudTile& t=j<split?dead:alive;unsigned k=j*t.w+i;
    if(t.mask[k])((unsigned short*)(src.data()+(y+j)*pitch))[x+i+(j<split?shift:0)]=t.low[k];
   }
   before=src;mm_hud_present(&primary,dst.data());assert(src==before);
   unsigned changed_top=0,changed_bottom=0;
   for(unsigned j=0;j<alive.h;j++)for(unsigned i=0;i<alive.w;i++){
    unsigned short c=((unsigned short*)(dst.data()+(y+j)*2*pitch))[(x+i+(j<split?shift:0))*2];
    if(c!=0x2727){if(j<split)changed_top++;else changed_bottom++;}
   }
   if(changed_top<=100 || changed_bottom<=100){printf("Health pair%u split%u: top%u bottom%u selected%d\n",pair,split,changed_top,changed_bottom,mm_hud_cache[0].tile);return 3;}health_cases++;
  }
 }
 fclose(pairs);
 printf("%u real pack/native compositing cases passed; %u alive/dead health split cases passed; worst template search %.3f ms\n",cases,health_cases,worst);
}
