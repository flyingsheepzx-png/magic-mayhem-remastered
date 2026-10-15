// Bounded local A*: native occupancy, transition and route-record validators.
// Complete routes only; preserve macro navigation for distant/complex paths.
static bool local_route(void* u,int gx,int gy,int gz,int* output){
 if(global(0x6e1f0c)>1 || !field(u,4) || !field(u,0xe4) || field(u,0x5ec)!=2 ||
    field(u,0x104)!=0 || field(u,0x10c)!=0 ||
    *(unsigned char*)((char*)u+0x71c) || *(unsigned char*)((char*)u+0x723))return false;
 void* type=*(void**)((char*)u+0xac);
 if(!type || field(type,8)!=1 || field(type,0x44)!=1)return false;
 int x=field(u,8),y=field(u,12),z=field(u,16);
 int w=global(0x6c5494),h=global(0x6c5498),layers=global(0x6c549c);
 if(x<0||y<0||z<0||x>=w||y>=h||z>=layers||gx<0||gy<0||gz<0||gx>=w||gy>=h||gz>=layers)return false;
 int distance=max(abs(gx-x),abs(gy-y));
 if(distance<1 || distance>16 || abs(gx-x)>w/2 || abs(gy-y)>h/2)return false;
 struct Node{int x,y,z,g,f,parent;bool closed;};Node nodes[256];int count=1,found=-1;
 auto heuristic=[&](int a,int b){int dx=abs(gx-a),dy=abs(gy-b);return 10*max(dx,dy)+4*min(dx,dy);};
 nodes[0]={x,y,z,0,heuristic(x,y),-1,false};
 for(int expanded=0;expanded<256;++expanded){
  int current=-1;
  for(int i=0;i<count;++i)if(!nodes[i].closed && (current<0 || nodes[i].f<nodes[current].f ||
     (nodes[i].f==nodes[current].f && nodes[i].g>nodes[current].g)))current=i;
  if(current<0)return false;
  Node from=nodes[current];nodes[current].closed=true;
  if(from.x==gx && from.y==gy && from.z==gz){found=current;break;}
  for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy){
   if(!dx&&!dy)continue;int nx=from.x+dx,ny=from.y+dy;
   if(nx<0||ny<0||nx>=w||ny>=h||max(abs(nx-x),abs(ny-y))>16)continue;
   for(int nz=max(0,from.z-1);nz<=min(layers-1,from.z+1);++nz){
    int kind=5;
    if(((BlockedFn)0x522f50)(u,nx,ny,nz) ||
       !((TransitionFn)0x514360)(u,from.x,from.y,from.z,nx,ny,nz,&kind,0) || kind!=0)continue;
    int g=from.g+(dx&&dy?14:10),index=-1;
    for(int i=0;i<count;++i)if(nodes[i].x==nx&&nodes[i].y==ny&&nodes[i].z==nz){index=i;break;}
    if(index>=0 && nodes[index].g<=g)continue;
    if(index<0){if(count==256)return false;index=count++;}
    nodes[index]={nx,ny,nz,g,g+heuristic(nx,ny),current,false};
   }
  }
 }
 if(found<0)return false;
 int reverse[16],length=0;
 for(int i=found;nodes[i].parent>=0;i=nodes[i].parent){if(length==16)return false;reverse[length++]=i;}
 int result[0x83];memcpy(result,(char*)u+0x96b,sizeof(result));
 result[0]=gx;result[1]=gy;result[2]=gz;result[3]=0;result[4]=length;
 unsigned char shadow[0xe4b];memcpy(shadow,u,sizeof(shadow));int one[0x83];
 for(int i=0;i<length;++i){
  const Node& next=nodes[reverse[length-1-i]];
  field(shadow,8)=x;field(shadow,12)=y;field(shadow,16)=z;
  if(!((DirectRouteFn)0x513370)(shadow,next.x,next.y,next.z,one) ||
     one[3]!=0 || one[4]!=1 || one[5]!=next.x || one[6]!=next.y || one[7]!=next.z ||
     one[10]!=0 || one[11]!=0)return false;
  memcpy(result+5+i*7,one+5,28);x=next.x;y=next.y;z=next.z;
 }
 memcpy(output,result,sizeof(result));return true;
}
