// Native metadata and per-edge collision/support checks on an unambiguous
// projected straight corridor. A bounded prefix preserves the 16-node ABI.
static bool corridor_route(void* u,int gx,int gy,int gz,int* output) {
 if(global(0x6e1f0c)>1 || !field(u,4) || !field(u,0xe4) ||
    field(u,0x5ec)!=2 || field(u,0x104)!=0 || field(u,0x10c)!=0 ||
    *(unsigned char*)((char*)u+0x71c) || *(unsigned char*)((char*)u+0x723))return false;
 void* type=*(void**)((char*)u+0xac);
 if(!type || field(type,8)!=1 || field(type,0x44)!=1)return false;
 int x=field(u,8),y=field(u,12),z=field(u,16);
 int w=global(0x6c5494),h=global(0x6c5498),layers=global(0x6c549c);
 if(gx<0 || gy<0 || gz<0 || gx>=w || gy>=h || gz>=layers ||
    x<0 || y<0 || z<0 || x>=w || y>=h || z>=layers)return false;
 int dx=gx-x,dy=gy-y,length=max(abs(dx),abs(dy));
 // Restrict to grid axis/diagonal: no new line rasterization or wrap policy.
 if(length<1 || length>64 || (dx && dy && abs(dx)!=abs(dy)) ||
    abs(dx)>w/2 || abs(dy)>h/2)return false;
 int sx=(dx>0)-(dx<0),sy=(dy>0)-(dy<0);
 int result[0x83];memcpy(result,(char*)u+0x96b,sizeof(result));
 result[0]=gx;result[1]=gy;result[2]=gz;result[3]=0;result[4]=min(length,16);
 unsigned char shadow[0xe4b];memcpy(shadow,u,sizeof(shadow));
 int one[0x83];
 for(int i=0;i<length;i++) {
  int nx=x+sx,ny=y+sy,nz=-1;
  for(int candidate=max(0,z-1);candidate<=min(layers-1,z+1);candidate++) {
   int kind=5;
   // Native transition includes support/headroom and handles ramp surfaces.
   // The extra flat-cell clearance helper rejects valid descending ramp tiles.
   if(((BlockedFn)0x522f50)(u,nx,ny,candidate) ||
      !((TransitionFn)0x514360)(u,x,y,z,nx,ny,candidate,&kind,0) || kind!=0)continue;
   if(nz!=-1)return false; // overlapping/ambiguous floors stay native
   nz=candidate;
  }
  if(nz<0)return false;
  field(shadow,8)=x;field(shadow,12)=y;field(shadow,16)=z;
  if(!((DirectRouteFn)0x513370)(shadow,nx,ny,nz,one) ||
     one[3]!=0 || one[4]!=1 || one[5]!=nx || one[6]!=ny || one[7]!=nz ||
     one[10]!=0 || one[11]!=0)return false;
  if(i<16)memcpy(result+5+i*7,one+5,28);
  x=nx;y=ny;z=nz;
 }
 if(x!=gx || y!=gy || z!=gz)return false;
 memcpy(output,result,sizeof(result));return true;
}
static bool loaded_route_pending[1024];
static void __cdecl mark_loaded_route(void* u) {
 int i=state_index(u);if(i>=0)loaded_route_pending[i]=true;
}
