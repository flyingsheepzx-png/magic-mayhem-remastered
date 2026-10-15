"""Whole41d270 two active owners, asymmetric relation/filter matrices."""
import itertools,json
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA
from verify_ai_danger_cell_effects import stage

def fixture(count,relations,filters):
    u=machine();u.mem_map(0,4096);m=0x2010000;head=0x2028000;nil=head+0x40
    definition=0x2040000;cells=0x2050000;units=0x2080000;bump=[0x2100000]
    owners=(0,7);unit_owners=(0,7,0,7,0,7,0)
    relation={(0,0):1,(7,7):1,(0,7):int(bool(relations&1)),(7,0):int(bool(relations&2))}
    filtering={(0,7):int(bool(filters&1)),(7,0):int(bool(filters&2))}
    put(u,nil,'5I',nil,nil,nil,0,1);put(u,head,'5I',head,nil,head,0,0)
    put(u,0x5faf20,'I',nil);put(u,m+0x1208c,'I',head);put(u,m+0x12098,'B',1)
    for slot in range(8):put(u,0x643a80+slot*0x154+0xc,'i',-1)
    for owner,index in ((0,0),(7,1)):
        p=0x643a80+owner*0x154;put(u,p,'II',1,0);put(u,p+0xc,'I',index)
        for other in owners:
            put(u,p+0x18+other,'B',relation[owner,other])
            if owner!=other:put(u,p+0x28+other,'B',filtering[owner,other])
    put(u,0x6def58,'I',units);put(u,0x6def5c,'I',125)
    put(u,0x6eaf08,'III',cells,count,count);stage(u,[(69,0,10),(70,0,10),(91,0,10)],0)
    put(u,0x6eaf08+0x6a11,'III',0x20f0000,0x20f0000,0x20f1000)
    put(u,definition+8,'II',1,1)
    for index,owner in enumerate(unit_owners):
        for offset,value in ((4,1),(0xe4,100),(0xac,definition),(0xe8,8192),(0x174,owner)):
            put(u,units+index*0xe4b+offset,'I',value)
    for i in range(3):
        edge=cells+i*0x294+0x10;put(u,edge,'II',1,i+1);put(u,edge+8,'BB',1,1)
    sequences={o:[i for i,who in enumerate(unit_owners) if who==o or (relation[who,o] and filtering[who,o])] for o in owners}
    values={o:[160 if relation[o,unit_owners[i]] else 0 for i in sequences[o]] for o in owners}
    pending={o:0 for o in owners};position={o:0 for o in owners};published={o:0 for o in owners}
    alloc=set();freed=set();commits=[];publications=[];round_units=[0]
    for p in (0x597850,0x597870):u.mem_write(p,b'\xc3')
    def hook(uc,address,size,user):
        if address==0x597850:
            assert word(uc,uc.reg_read(UC_X86_REG_ESP)+4)==20
            p=bump[0];bump[0]+=32;alloc.add(p);uc.reg_write(UC_X86_REG_EAX,p)
        elif address==0x597870:
            p=word(uc,uc.reg_read(UC_X86_REG_ESP)+4);assert p in alloc and p not in freed;freed.add(p)
        elif address==0x41dbc0:
            owner=word(uc,m+0x12099);pos=position[owner];index=sequences[owner][pos]
            assert word(uc,m+0x1209d)==index and uc.reg_read(UC_X86_REG_EAX)==values[owner][pos]
            assert word(uc,m+0x120a9)==pending[owner]
            pending[owner]+=values[owner][pos];position[owner]+=1;round_units[0]+=1
            for i in range(count):
                v=min(255,position[owner]*16) if i<3 else 0
                assert list(uc.mem_read(cells+i*0x294+0x28c,7))==[v,v,0,0,0,0,0]
            commits.append(dict(owner=owner,unit=index,value=values[owner][pos]))
        elif address==0x41d476 and word(uc,m+0x12099) in owners:
            owner=word(uc,m+0x12099);assert position[owner]==len(sequences[owner])
            wizard=units+(0 if owner==0 else 1)*0xe4b
            assert word(uc,wizard+0x926)==sum(values[owner])==pending[owner]
            published[owner]+=1
            for i in range(count):
                for slot in range(8):
                    expected=[0]*7
                    if slot in owners and published[slot]:
                        v=min(255,len(sequences[slot])*16) if i<3 else 0
                        expected=[v,v,0,*([30,20,25] if relation[slot,0] else [0,0,0]),0]
                    assert list(uc.mem_read(cells+i*0x294+0x24c+slot*7,7))==expected
                assert bytes(uc.mem_read(cells+i*0x294+0x28c,7))==bytes(7)
            publications.append(dict(owner=owner,total=pending[owner],selected_units=list(sequences[owner])))
            pending[owner]=0;position[owner]=0
    u.hook_add(UC_HOOK_CODE,hook)
    for _ in range(20):
        round_units[0]=0;call(u,0x41d270,m,[]);assert round_units[0]<=4
    assert all(n>=2 for n in published.values())
    assert len(alloc-freed)==word(u,m+0x12094)
    return dict(cells=count,relations=relations,filters=filters,sequences=sequences,contributions=values,publication_counts=published,publications=publications,commits=len(commits))

def verify():
    cases=[fixture(*v) for v in itertools.product((4,33),range(4),range(4))]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='32 whole41d270 two-active-owner0/7 fixtures,20calls each,7active units in125pool,4/33cells,persistent69/70/91 effects. OnlyCRTalloc/free doubled. All asymmetricrelation18/filter28 masks:foreign selection reads sourceprofile->evaluatedowner;529e40 contribution/effect inclusion reads evaluatedprofile->source/effectowner,so admittedforeignunit canyield0. Independently checksselectedsequence/value/total/all8 publishedsegments/sharedscratchclear/4unitbudget,atleast2publications perowner. Otherprofiles/game/network initialization/relationship labels/actualcaller remain pending.')
    (ROOT/'modernization/docs/ai-danger-multiowner-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),whole_calls=20*len(cases)))

if __name__=='__main__':verify()
