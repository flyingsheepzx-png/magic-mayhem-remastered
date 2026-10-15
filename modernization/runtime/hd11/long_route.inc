// Bounded full-map A*; native validators and 16-point engine route ABI retained.
struct LongPoint{int x,y,z;};
struct LongCache{void* unit;int id,map,w,h,layers,gx,gy,gz,count;LongPoint path[512];};
static LongCache long_caches[32];
static void long_route_forget(void* u){for(auto& c:long_caches)if(c.unit==u)c.unit=nullptr;}
static bool long_route(void* u,int gx,int gy,int gz,int* output){
 if(global(0x6e1f0c)>1 || !field(u,4)||!field(u,0xe4)||field(u,0x5ec)!=2||field(u,0x104)||field(u,0x10c)||
    *(unsigned char*)((char*)u+0x71c)||*(unsigned char*)((char*)u+0x723))return false;
 void* type=*(void**)((char*)u+0xac);if(!type||field(type,8)!=1||field(type,0x44)!=1)return false;
 int x=field(u,8),y=field(u,12),z=field(u,16),w=global(0x6c5494),h=global(0x6c5498),layers=global(0x6c549c),map=global(0x6c54dc);
 if(w<1||h<1||layers<1||(uint64_t)w*h*layers>4000000 || x<0||y<0||z<0||gx<0||gy<0||gz<0||x>=w||y>=h||z>=layers||gx>=w||gy>=h||gz>=layers)return false;
 if(x==gx&&y==gy&&z==gz)return false;
 LongCache& cache=long_caches[(unsigned)field(u,0)%32];int cursor=-1;
 if(cache.unit==u&&cache.id==field(u,0)&&cache.map==map&&cache.w==w&&cache.h==h&&cache.layers==layers&&cache.gx==gx&&cache.gy==gy&&cache.gz==gz)
  for(int i=0;i<cache.count;++i)if(cache.path[i].x==x&&cache.path[i].y==y&&cache.path[i].z==z){cursor=i;break;}
 if(cursor<0){
  struct Node{int x,y,z,g,parent,heap;bool closed;};
  static Node nodes[16384];static int slots[32768],heap[16384];int count=1,heap_count=1,found=-1;
  memset(slots,0xff,sizeof slots);nodes[0]={x,y,z,0,-1,0,false};heap[0]=0;
  auto key=[&](int a,int b,int c){return a+w*(b+h*c);};
  auto heuristic=[&](const Node& n){int dx=abs(gx-n.x),dy=abs(gy-n.y);dx=min(dx,w-dx);dy=min(dy,h-dy);return 10*max(dx,dy)+4*min(dx,dy);};
  auto better=[&](int a,int b){int fa=nodes[a].g+heuristic(nodes[a]),fb=nodes[b].g+heuristic(nodes[b]);return fa<fb||(fa==fb&&nodes[a].g>nodes[b].g);};
  auto slot=[&](int a,int b,int c){unsigned k=(unsigned)key(a,b,c),s=(k*2654435761u)&32767;while(slots[s]>=0 && key(nodes[slots[s]].x,nodes[slots[s]].y,nodes[slots[s]].z)!=(int)k)s=(s+1)&32767;return s;};
  slots[slot(x,y,z)]=0;
  auto lift=[&](int index){int pos=nodes[index].heap;while(pos>0){int parent=(pos-1)/2;if(!better(index,heap[parent]))break;heap[pos]=heap[parent];nodes[heap[pos]].heap=pos;pos=parent;}heap[pos]=index;nodes[index].heap=pos;};
  for(int expanded=0;expanded<8192 && heap_count;++expanded){
   int current=heap[0],last=heap[--heap_count];if(heap_count){int pos=0;while(pos*2+1<heap_count){int child=pos*2+1;if(child+1<heap_count&&better(heap[child+1],heap[child]))++child;if(!better(heap[child],last))break;heap[pos]=heap[child];nodes[heap[pos]].heap=pos;pos=child;}heap[pos]=last;nodes[last].heap=pos;}
   nodes[current].heap=-1;nodes[current].closed=true;Node from=nodes[current];
   if(from.x==gx&&from.y==gy&&from.z==gz){found=current;break;}
   for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy){if(!dx&&!dy)continue;int nx=(from.x+dx+w)%w,ny=(from.y+dy+h)%h;
    for(int nz=max(0,from.z-1);nz<=min(layers-1,from.z+1);++nz){
     int kind=5;if(((BlockedFn)0x522f50)(u,nx,ny,nz)||!((TransitionFn)0x514360)(u,from.x,from.y,from.z,nx,ny,nz,&kind,0)||kind!=0)continue;
     unsigned s=slot(nx,ny,nz);int index=slots[s],cost=from.g+(dx&&dy?14:10);
     if(index>=0 && nodes[index].g<=cost)continue;
     if(index<0){if(count==16384)return false;index=count++;slots[s]=index;nodes[index]={nx,ny,nz,cost,current,heap_count,false};heap[heap_count++]=index;}
     else {nodes[index].g=cost;nodes[index].parent=current;if(nodes[index].heap<0){nodes[index].heap=heap_count;heap[heap_count++]=index;}nodes[index].closed=false;}
     lift(index);
    }
   }
  }
  if(found<0)return false;
  int reverse[512],length=0;for(int i=found;i>=0;i=nodes[i].parent){if(length==512)return false;reverse[length++]=i;}
  cache.unit=u;cache.id=field(u,0);cache.map=map;cache.w=w;cache.h=h;cache.layers=layers;cache.gx=gx;cache.gy=gy;cache.gz=gz;cache.count=length;
  for(int i=0;i<length;++i){Node& n=nodes[reverse[length-1-i]];cache.path[i]={n.x,n.y,n.z};}cursor=0;
 }
 int length=min(16,cache.count-1-cursor);if(length<1)return false;
 int result[0x83];memcpy(result,(char*)u+0x96b,sizeof result);result[0]=gx;result[1]=gy;result[2]=gz;result[3]=0;result[4]=length;
 unsigned char shadow[0xe4b];memcpy(shadow,u,sizeof shadow);int one[0x83];
 for(int i=0;i<length;++i){const auto& p=cache.path[cursor+i+1];int kind=5;
  if(((BlockedFn)0x522f50)(u,p.x,p.y,p.z)||!((TransitionFn)0x514360)(u,x,y,z,p.x,p.y,p.z,&kind,0)||kind!=0){cache.unit=nullptr;return false;}
  field(shadow,8)=x;field(shadow,12)=y;field(shadow,16)=z;
  if(!((DirectRouteFn)0x513370)(shadow,p.x,p.y,p.z,one)||one[3]!=0||one[4]!=1||one[5]!=p.x||one[6]!=p.y||one[7]!=p.z||one[10]!=0||one[11]!=0){cache.unit=nullptr;return false;}
  memcpy(result+5+i*7,one+5,28);x=p.x;y=p.y;z=p.z;
 }
 memcpy(output,result,sizeof result);return true;
}
