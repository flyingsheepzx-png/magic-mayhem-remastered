"""Native51a880 per-owner visibility and522340 owner creature count, no doubles."""
import itertools,json,struct
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA
from verify_ai_profile_selection import BASE,SIZE,word

def visibility(owner,friends,sharing,value):
    u=machine();unit=0x2010000;u.mem_write(unit,b'\xa5'*0xe4b);u.mem_write(BASE,b'\xa5'*SIZE)
    put(u,unit+0x174,'I',owner)
    for i in range(8):
        put(u,BASE+owner*0x154+0x18+i,'B',value if friends>>i&1 else 0)
        put(u,BASE+owner*0x154+0x20+i,'B',value if sharing>>i&1 else 0)
    before=bytes(u.mem_read(BASE,SIZE));expected=bytearray(u.mem_read(unit,0xe4b))
    for i in range(8):
        word(expected,0x24+4*i,30 if i==owner or friends>>i&1 and sharing>>i&1 else 0)
        word(expected,0x48+4*i,0)
    call(u,0x51a880,unit,[])
    assert bytes(u.mem_read(unit,0xe4b))==expected and bytes(u.mem_read(BASE,SIZE))==before
    return dict(owner=owner,friends=friends,sharing=sharing,value=value)

def count(owner,active,health,excluded,foreign,duplicate,size=8,present=True):
    u=machine();pool=0x2010000;definition=0x2040000
    u.mem_write(pool,b'\xa5'*(0xe4b*max(1,size)));u.mem_write(BASE,b'\xa5'*SIZE)
    put(u,0x6def58,'I',pool);put(u,0x6def5c,'I',max(1,size));put(u,0x6df180,'I',size)
    put(u,0x644520,'i',-1);put(u,BASE+owner*0x154,'I',1)
    put(u,BASE+owner*0x154+12,'i',0 if present else -1)
    put(u,pool+0xac,'I',definition);put(u,definition,'I',0);put(u,pool+0x7c,'I',0)
    selected=[]
    for i in range(max(1,size)):
        p=pool+i*0xe4b;put(u,p,'I',100 if i==0 or duplicate>>i&1 else 100+i)
        put(u,p+4,'I',int(bool(active>>i&1)));put(u,p+0xe4,'I',10 if health>>i&1 else 0)
        put(u,p+0x174,'I',(owner+1)%8 if i and foreign>>i&1 else owner)
        put(u,p+0xa8,'I',27 if excluded>>i&1 else 1)
        if i and active>>i&1 and health>>i&1 and not excluded>>i&1 and not foreign>>i&1 and not duplicate>>i&1:selected.append(i)
    expected=bytearray(u.mem_read(pool,0xe4b*max(1,size)));before=bytes(u.mem_read(BASE,SIZE))
    if present:word(expected,0x8f5,len(selected))
    call(u,0x522340,pool,[])
    assert bytes(u.mem_read(pool,len(expected)))==expected
    assert bytes(u.mem_read(BASE,SIZE))==before
    return dict(owner=owner,active=active,health=health,excluded=excluded,foreign=foreign,duplicate=duplicate,size=size,present=present,counted_slots=selected)

def verify():
    views=[visibility(*v) for v in itertools.product(range(8),(0,1,85,170,255),(0,1,85,170,255),(1,255))]
    counts=[count(*v) for v in itertools.product(range(8),(0,85,170,255),(0,85,170,255),(0,85,255),(0,170,255),(0,85,255))]
    boundaries=[count(o,0xffffffff,0xffffffff,0,0,0,size=n,present=p) for o,n,p in itertools.product((0,7),(0,1,32),(False,True))]
    report=dict(result='passed',engine_sha256=SHA,visibility_cases=views,count_cases=counts,boundary_cases=boundaries,
        scope='400 whole51a880 and3456+12 whole522340 no-double cases. Visibilitysetsunit24[owner]=30,other24=30 iffownerprofile18&20 truthy,all48slotszero;fullunit/profile snapshots. Countreal466870 scans6df180slots,active4/health nonzero,samewizardowner,differentunit0ID,typea8!=27;writeswizard8f5 only. All8owners/asymmetric masks/truth255/duplicateIDs/count0-1-32/missingwizard. CountUI suffix suppressed bylocal644520=-1;capacity8f1 production/UI/alltypes/invalidglobals/ownershipwhole/save/network pending.')
    (ROOT/'modernization/docs/ai-owner-bookkeeping-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',visibility=len(views),count=len(counts)+len(boundaries)))

if __name__=='__main__':verify()
