"""Whole4202e0 effect-list cell accumulation, no doubles."""
import itertools,json
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA

def stage(u,effects,owner,relation=1):
    head=0x2070000;put(u,0x6898e4,'I',head)
    nodes=[head+0x100+i*0x400 for i in range(len(effects))]
    put(u,head,'I',nodes[0] if nodes else head)
    put(u,0x6c5494,'II',4096,4096)
    for i,(kind,x,radius) in enumerate(effects):
        node=nodes[i];effect=node+0x40
        put(u,node,'III',nodes[i+1] if i+1<len(nodes) else head,0,effect)
        put(u,effect+8,'3i',x,0,0);put(u,effect+0x4c,'I',kind)
        put(u,effect+0x212,'I',0)
        put(u,0x6b13c9+721*kind,'I',radius)
    put(u,0x643a80+owner*0x154+0x18,'B',relation)

def fixture(effects,owner,relation,initial):
    u=machine();cells=0x2040000;put(u,0x6eaf08,'I',cells);put(u,0x6eaf0c,'I',1)
    stage(u,effects,owner,relation)
    put(u,cells+4,'3i',0,0,0);u.mem_write(cells+0x28c,bytes([initial])*7)
    before=bytes(u.mem_read(cells,0x294));call(u,0x4202e0,0,[0,owner])
    expected=bytearray(before)
    for kind,x,radius in effects:
        if abs(x)<=radius and relation and kind in (69,70,91):
            offset,inc={69:(0x28f,30),70:(0x290,20),91:(0x291,25)}[kind]
            expected[offset]=min(255,expected[offset]+inc)
    assert bytes(u.mem_read(cells,0x294))==bytes(expected)
    return dict(effects=effects,owner=owner,relation=relation,initial=initial,output=list(expected[0x28c:0x293]))

def verify():
    cases=[fixture([(kind,x,10)]*repeats,owner,relation,initial)
        for kind,x,repeats,owner,relation,initial in itertools.product((69,70,91,68),(9,10,11),(1,3),(0,7),(0,1,255),(0,224,230,235,250,255))]
    cases.extend(fixture(effects,owner,1,224) for owner in range(8) for effects in ([],[(69,0,10),(70,0,10),(91,0,10)]))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='Whole4202e0 no doubles with real429b50 list dereference/coordinate wrappers/419920 wrapped-distance radius test; synthetic circular effect list and definitions. Type69 adds30 to28f,type70 adds20 to290,type91 adds25 to291,saturating255,only within radius inclusive and profile relation nonzero. Other types unchanged. All cell bytes checked;empty/mixed/repeated lists and radius boundary. Installed effect names/radii/producers,map consumers,negative/overflow/invalid pointers pending.')
    (ROOT/'modernization/docs/ai-danger-cell-effects-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
