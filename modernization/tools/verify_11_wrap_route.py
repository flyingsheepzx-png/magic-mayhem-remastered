"""Compiled wrapped long path against save20 native seam transitions/records."""
import json,struct,pefile
from unicorn.x86_const import *
import analyze_test18_corridor as a
import build_remastered_11 as b
OUT=b.ROOT/'modernization/build/remastered-1.1-wrap-route-v1'
P=pefile.PE(str(OUT/'repath.dll'));BASE=P.OPTIONAL_HEADER.ImageBase
LINES=(OUT/'repath.map').read_text().splitlines()
def sym(name):return int(next(x for x in LINES if '?'+name+'@@' in x).split()[2],16)
def setup():
 a.RUN=b.ROOT/'modernization/logs/remastered-ui/save20-route-before';n=a.Terrain()
 n.u.mem_map(BASE,(P.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);n.u.mem_write(BASE,P.get_memory_mapped_image());return n
def route(n,g):
 n.u.mem_write(0x1806000,b'\xa5'*524)
 ok=n.call(sym('long_route'),[n.unit,*g,0x1806000],0,10000000)&255
 return ok,struct.unpack('<131i',n.u.mem_read(0x1806000,524))
def main():
 n=setup();ok,r=route(n,(0,56,5));assert ok and r[:3]==(0,56,5) and r[3]==0 and 0<r[4]<=16
 path=[r[5+i*7:8+i*7] for i in range(r[4])];assert path[-1]==(0,56,5) and any(x==99 for x,y,z in path)
 start=tuple(struct.unpack('<3i',n.u.mem_read(n.unit+8,12)));assert path[0][0]>start[0],(start,path)
 prev=start;checks=1
 for p in path:
  n.w(0x1805000,5);assert n.call(0x514360,[*prev,*p,0x1805000,0],n.unit) and struct.unpack('<i',n.u.mem_read(0x1805000,4))[0]==0
  assert not n.call(0x522f50,list(p),n.unit)
  dx=abs(p[0]-prev[0]);dy=abs(p[1]-prev[1]);assert min(dx,100-dx)<=1 and min(dy,100-dy)<=1;prev=p;checks+=1
 # Reverse boundary direction and cache continuation from99→0.
 n=setup();n.w(n.unit+8,0);n.w(n.unit+12,59);n.w(n.unit+16,5)
 ok,rback=route(n,(99,59,5));assert ok and rback[5:8]==(99,59,5) and rback[4]==1;checks+=1
 n=setup();route(n,(0,56,5));n.w(n.unit+8,99);n.w(n.unit+12,57);n.w(n.unit+16,5)
 ok,tail=route(n,(0,56,5));assert ok and tail[5:8]==(0,56,5);checks+=1
 # Fully solid goal rejected; bounds and multiplayer exclusions untouched.
 for offset,value in [(0x6e1f0c,2),(n.unit+0x5ec,14),(n.typ+8,2)]:
  n=setup();n.w(offset,value);assert not route(n,(0,56,5))[0];checks+=1
 for goal in [(-1,56,5),(100,56,5),(0,100,5),(0,56,28)]:
  n=setup();assert not route(n,goal)[0];checks+=1
 report=dict(result='passed',checks=checks,module_sha256=b.sha(OUT/'repath.dll'),start=start,path=path,native_seam_validation=True,runtime_acceptance='pending user save20 testing')
 (OUT/'wrap-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
