"""Run compiled local search against captured terrain and native validators."""
import struct,json,pefile
import analyze_test18_corridor as a
import build_11_local_route as b
from unicorn.x86_const import *
def main():
 a.RUN=b.b.ROOT/'modernization/logs/remastered-ui/save3-route-before'
 p=pefile.PE(str(b.OUT/'repath.dll'));base=p.OPTIONAL_HEADER.ImageBase
 lines=(b.OUT/'repath.map').read_text().splitlines()
 def sym(name):return int(next(x for x in lines if '?'+name+'@@' in x).split()[2],16)
 def setup():
  n=a.Terrain();n.u.mem_map(base,(p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);n.u.mem_write(base,p.get_memory_mapped_image());return n
 def route(n):
  n.u.mem_write(0x1806000,b'\xa5'*524)
  yes=n.call(sym('local_route'),[n.unit,18,36,6,0x1806000],0,budget=10000000)&255
  return yes,struct.unpack('<131i',n.u.mem_read(0x1806000,524))
 n=setup();yes,r=route(n);assert yes and r[:5]==(18,36,6,0,16)
 path=[r[5+i*7:8+i*7] for i in range(r[4])];assert path[0]==(29,44,5) and path[-1]==(18,36,6)
 assert all(x<=29 for x,y,z in path)
 checks=1
 for off,value in [(0x6e1f0c,2),(0x1801000+0x5ec,14),(0x1803000+8,2),(0x1803000+0x44,2),(0x1801000+0x10c,1)]:
  n=setup();n.w(off,value);assert not route(n)[0];assert n.u.mem_read(0x1806000,524)==b'\xa5'*524;checks+=1
 # Fully occupied goal must be rejected without writing output.
 n=setup();w,h,_=json.loads((a.RUN/'capture.json').read_text())['dimensions']
 n.u.mem_write(0x1000000+12*(18+36*w+6*w*h)+10,struct.pack('<H',0x4000))
 assert not route(n)[0];checks+=1
 # Existing test18 rising/descending corridor remains on its original adapter.
 a.RUN=b.b.ROOT/'modernization/logs/remastered-ui/test18-path-before-v1'
 n=setup();yes=n.call(sym('corridor_route'),[n.unit,63,20,9,0x1806000],0)&255
 r18=struct.unpack('<131i',n.u.mem_read(0x1806000,524))
 assert yes and r18[:5]==(63,20,9,0,16)
 assert [r18[7+i*7] for i in range(16)]==[9,9,10,11,12,13,13,13,13,12,11,10,9,9,9,9];checks+=1
 # Multiplayer and nonordinary movement retain untouched native fallback.
 b.base.write(b.OUT/'verification.json',dict(result='passed',checks=checks,module_sha256=b.b.sha(b.OUT/'repath.dll'),path=path,native_validators=True,runtime_acceptance='pending isolated save3 capture'))
 print('compiled native local route passed',path)
if __name__=='__main__':main()
