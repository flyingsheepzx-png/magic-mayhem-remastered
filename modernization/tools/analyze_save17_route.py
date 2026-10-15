"""Search captured save3 terrain using the exact native transition validator."""
import json,heapq,struct
import analyze_test18_corridor as a
import build_remastered_11 as b
a.RUN=b.ROOT/'modernization/logs/remastered-ui/save17-route-before'
def search():
 n=a.Terrain();from emulate_terrain_diagonal import Native;Native.patch(n,b.TARGET/'runtime/terrain_diagonal.dll');start=tuple(struct.unpack('<3i',n.u.mem_read(n.unit+8,12)));goal=tuple(struct.unpack('<3i',n.u.mem_read(n.unit+0x96b,12)))
 dims=json.loads((a.RUN/'capture.json').read_text())['dimensions'];q=[(0,0,start)];cost={start:0};prev={};calls=0
 while q:
  _,g,pos=heapq.heappop(q)
  if g!=cost[pos]:continue
  if pos==goal:break
  for dx,dy in [(x,y) for x in (-1,0,1) for y in (-1,0,1) if x or y]:
   x,y,z=pos
   for zz in range(max(0,z-2),min(dims[2]-1,z+2)+1):
    nxt=(x+dx,y+dy,zz)
    if not (0<=nxt[0]<dims[0] and 0<=nxt[1]<dims[1]):continue
    if max(abs(nxt[0]-start[0]),abs(nxt[1]-start[1]))>100:continue
    n.w(n.unit+8,x);n.w(n.unit+12,y);n.w(n.unit+16,z)
    if n.call(0x522f50,list(nxt),n.unit):continue
    n.w(0x1805000,5);calls+=1
    if not n.call(0x514360,[*pos,*nxt,0x1805000,0],n.unit):continue
    value=g+(14 if dx and dy else 10)
    if value>=cost.get(nxt,100000):continue
    cost[nxt]=value;prev[nxt]=pos
    h=10*max(abs(nxt[0]-goal[0]),abs(nxt[1]-goal[1]))+4*min(abs(nxt[0]-goal[0]),abs(nxt[1]-goal[1]))
    heapq.heappush(q,(value+h,value,nxt))
 else:
  print('no route',len(cost),'layers',sorted(set(p[2] for p in cost)), 'nearest',sorted(cost,key=lambda p:max(abs(p[0]-goal[0]),abs(p[1]-goal[1]))+abs(p[2]-goal[2]))[:15]);b.write(a.RUN/'reachable.json',dict(cost=[[list(p),v] for p,v in cost.items()]));return
 path=[goal]
 while path[-1]!=start:path.append(prev[path[-1]])
 path.reverse();print(dict(start=start,goal=goal,path=path,cost=cost[goal],calls=calls,nodes=len(cost)))
 b.write(a.RUN/'native-shortest.json',dict(start=start,goal=goal,path=path,cost=cost[goal],calls=calls,nodes=len(cost)))
if __name__=='__main__':search()
