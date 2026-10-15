"""Compiled terrain policy on captured save13 cells and earlier ramp fixtures."""
import struct,json
import analyze_test18_corridor as a
from emulate_terrain_diagonal import Native
import build_11_half_stair as b
from install_11_minimap_v2 import resources

def main():
 run=b.b.ROOT/'modernization/logs/remastered-ui/save13-route-before';a.RUN=run
 def setup(fixed=True):
  n=a.Terrain();Native.patch(n,b.OUT/'terrain_diagonal.dll' if fixed else b.base.DEST/'runtime/terrain_diagonal.dll');return n
 def edge(n,start,end):
  for off,value in zip([8,12,16],start):n.w(n.unit+off,value)
  n.w(0x1805000,5)
  yes=n.call(0x514360,[*start,*end,0x1805000,0],n.unit)
  kind=struct.unpack('<i',n.u.mem_read(0x1805000,4))[0];return bool(yes) and kind==0
 start,end=(69,35,6),(70,35,7);checks=[]
 def test(label,value):assert value,label;checks.append(label)
 test('original roof-side false rejection reproduced',not edge(setup(False),start,end))
 test('actual half stair ascent',edge(setup(),start,end))
 test('actual half stair descent',edge(setup(),end,start))
 dims=json.loads((run/'capture.json').read_text())['dimensions'];w,h,_=dims
 def cell(x,y,z):return 0x1000000+12*(x+y*w+z*w*h)
 for label,x,y,z in [('source headroom',69,35,8),('destination headroom',70,35,8)]:
  n=setup();n.u.mem_write(cell(x,y,z)+10,struct.pack('<H',0x4000));test(label,not edge(n,start,end))
 n=setup();n.u.mem_write(cell(70,35,7)+4,struct.pack('<H',1));n.u.mem_write(cell(70,35,7)+10,struct.pack('<H',3));test('occupied destination',not edge(n,start,end))
 n=setup();n.u.mem_write(cell(70,35,6),b'\0\0');test('unsupported destination',not edge(n,start,end))
 for height in [0,4,12,16]:
  n=setup();n.w(0x1400000+1381*0x164+0x94,height)
  test('other stair height preserves original '+str(height),edge(n,start,end)==edge(setup_old_height(height),start,end))
 for field,value in [(0x6e1f0c,2),(0x1803000+8,2),(0x1803000+0x44,2)]:
  n=setup();n.w(field,value);old=setup(False);old.w(field,value);test('excluded profile '+hex(field),edge(n,start,end)==edge(old,start,end))
 # Independent retained test18 rising/descending ramps, both directions/modes.
 a.RUN=b.b.ROOT/'modernization/logs/remastered-ui/test18-path-before-v1'
 cases=0
 for players in (1,2):
  for width in (1,2):
   for height in (1,2,4,6,8):
    old,fixed=setup(False),setup()
    for n in (old,fixed):n.w(0x6e1f0c,players);n.w(n.typ+8,width);n.w(n.typ+12,height)
    for p,q in [((63,37,9),(63,36,10)),((63,36,10),(63,37,9)),((63,28,13),(63,27,12)),((63,27,12),(63,28,13)),((63,39,9),(63,38,9))]:
     assert edge(old,p,q)==edge(fixed,p,q);cases+=1
 a.RUN=run
 # Neighbor edge audit: all newly accepted edges must be adjacent half stairs.
 new=[];audited=0;old,fixed=setup(False),setup()
 for x in range(68,71):
  for y in range(34,37):
   for z in [6,7]:
    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1)]:
     for dz in [-1,0,1]:
      p=(x,y,z);q=(x+dx,y+dy,z+dz);before=edge(old,p,q);after=edge(fixed,p,q);audited+=1
      if before:assert after
      if after and not before:
       assert abs(dx)+abs(dy)==1 and abs(dz)==1;new.append([p,q])
 test('only intended local stair edges added',len(new)>0)
 for name in ['candidate.exe','release.exe']:assert resources(b.OUT/name)==resources(b.base.DEST/b.base.ENTRY)
 b.b.write(b.OUT/'verification.json',dict(result='passed',terrain_sha256=b.b.sha(b.OUT/'terrain_diagonal.dll'),checks=checks,old_regression_cases=cases,neighbor_edges_audited=audited,new_edges=new,save13_runtime_verified=False,engine_sha256=a.b.sha(a.b.TARGET/'runtime/Chaos-Wide169-engine.exe'),runtime_acceptance='pending authorized isolated save13 comparison'))
 print(len(checks),'checks;',cases,'prior cases;',audited,'neighbor edges;',len(new),'new stair edges')

def setup_old_height(height):
 n=a.Terrain();Native.patch(n,b.base.DEST/'runtime/terrain_diagonal.dll');n.w(0x1400000+1381*0x164+0x94,height);return n

if __name__=='__main__':main()
