"""Whole542810 greedy progress test with preallocated native vector,no doubles."""
import json,itertools,struct
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

SCENARIOS=(
    ('straight',((0,0),(10,0),(20,0),(30,0)),((0,1),(1,2),(2,3))),
    ('away_detour',((0,0),(-10,0),(0,10),(10,0)),((0,1),(1,2),(2,3))),
    ('equal_first',((0,0),(10,10),(10,-10),(20,0)),((0,1),(0,2),(1,3),(2,3))),
    ('equal_step',((0,0),(0,10),(10,10),(10,0)),((0,1),(1,2),(2,3))),
    ('disconnected',((0,0),(10,0),(20,0),(30,0)),()),
)

def fixture(name,coordinates,edges,gate,start,target):
    u=machine();obj=0x6eaf08;cells=0x2040000;vector=0x2090000;desc=0x2020000;out=desc+64
    put(u,obj,'III',cells,len(coordinates),len(coordinates));put(u,0x6c5494,'II',4096,4096)
    put(u,obj+0x6a11,'III',vector,vector,vector+256)
    put(u,desc,'4I',1,1,0,0);put(u,out,'I',0x11223344)
    for i,(x,y) in enumerate(coordinates):put(u,cells+i*0x294+4,'3i',x,y,0)
    slots={}
    for src,dst in edges:
        j=slots.get(src,0);slots[src]=j+1;edge=cells+src*0x294+0x10+j*28
        put(u,edge,'II',1,dst);put(u,edge+8,'BB',1,gate)
    original=bytes(u.mem_read(cells,len(coordinates)*0x294))
    result=call(u,0x542810,obj,[start,target,desc,out])
    def distance(i):
        x,y=coordinates[i];tx,ty=coordinates[target]
        dx=(x-tx+2048)%4096-2048;dy=(y-ty+2048)%4096-2048
        return dx*dx+dy*dy
    path=[start];current=start
    while current!=target:
        closest=current;best=distance(current)
        if 0<gate<128:
            for src,dst in edges:
                if src==current and distance(dst)<best:closest=dst;best=distance(dst)
        if closest==current:break
        path.append(closest);current=closest
    expected=int(current==target);assert result==expected
    expected_out=path[(len(path)-1)//2] if expected else 0xffffffff
    assert word(u,out)==expected_out
    n=(word(u,obj+0x6a15)-word(u,obj+0x6a11))//4
    actual=list(struct.unpack('<'+'I'*n,u.mem_read(vector,n*4)));assert actual==path,(name,start,target,actual,path)
    assert bytes(u.mem_read(cells,len(coordinates)*0x294))==original
    return dict(name=name,coordinates=coordinates,edges=edges,gate=gate,start=start,target=target,result=result,path=path,output=expected_out)

def verify():
    cases=[fixture(*scenario,gate,start,target) for scenario in SCENARIOS for gate,start,target in itertools.product((0,1,255),range(4),range(4))]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='240 whole542810 no-double cases,preallocated native scratch vector. Real vector clear/insert and coordinate wrappers/differences,movement descriptor index1 requirement1 mode0. Directed straight/away-detour/equal-branch/equal-step/disconnected topology,allstart/target pairs,gate0/1/255. Greedy strict distance reduction,first tie,middle path output,failed partial path,unchanged cells verified. This is not complete graph reachability;other descriptors/heights/overflow/vector growth/invalid inputs pending.')
    (ROOT/'modernization/docs/ai-greedy-reachability-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
