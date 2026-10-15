"""Whole41d270 multi-call native producer; CRT allocation/free doubles only."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA
from verify_ai_danger_cell_effects import stage

def fixture(active,count,kind,status,spatial=None,effects=False,owner=0,restart_at=None):
    u=machine();u.mem_map(0,4096);m=0x2010000;head=0x2028000;nil=head+0x40
    definition=0x2040000;cells=0x2050000;units=0x2080000;bump=[0x2100000]
    put(u,nil,'5I',nil,nil,nil,0,1);put(u,head,'5I',head,nil,head,0,0)
    put(u,0x5faf20,'I',nil);put(u,m+0x1208c,'I',head);put(u,m+0x12098,'B',1)
    for i in range(8):put(u,0x643a80+i*0x154+0xc,'i',-1)
    profile=0x643a80+owner*0x154
    put(u,profile,'II',1,0);put(u,profile+0xc,'I',0);put(u,profile+0x18+owner,'B',1)
    put(u,0x6def58,'I',units);put(u,0x6def5c,'I',125)
    put(u,0x6eaf08,'III',cells,count,count);stage(u,[(69,0,10),(70,0,10),(91,0,10)] if effects else [],owner)
    put(u,0x6eaf08+0x6a11,'III',0x20f0000,0x20f0000,0x20f1000)
    put(u,definition,'I',kind);put(u,definition+8,'II',1,1)
    for i in range(active):
        a=units+i*0xe4b
        for offset,value in ((4,1),(0xe4,100),(0xac,definition),(0xe8,8192),(0x174,owner),(0xde7,i%4 if spatial else 0),(0x7c,status)):
            put(u,a+offset,'I',value)
    edges=[(i+1,i) if spatial=='reverse' else (i,i+1) for i in range(3)]
    for src,dst in edges:
        edge=cells+src*0x294+0x10;put(u,edge,'II',1,dst);put(u,edge+8,'BB',1,1)
    if spatial:
        for i in range(4):put(u,cells+i*0x294+4,'i',i*10)
    for p,n in ((0x597850,0),(0x597870,0)):
        u.mem_write(p,b'\xc2'+struct.pack('<H',n) if n else b'\xc3')
    alloc=set();freed=set();events=[];round_events=[];pending=[0];next_unit=[0];reach=[0]
    contributions=[];selections=[];pending_total=[0];map_values=[0]*count
    for index in range(active):
        cell=index%4 if spatial else 0;selected={cell};frontier={cell}
        for _ in range(2 if kind==0 and status==0 else 1):
            frontier={dst for src,dst in edges if src in frontier};selected|=frontier
        reachable=not spatial or cell==0 or spatial=='reverse'
        value=(163840//(10000+2304*cell*10) if spatial else 16) if reachable else 0
        if status:value//=2
        contributions.append(value*10);selections.append(sorted(selected))
    def hook(uc,address,size,user):
        if address==0x597850:
            assert word(uc,uc.reg_read(UC_X86_REG_ESP)+4)==20
            p=bump[0];bump[0]+=32;alloc.add(p);uc.reg_write(UC_X86_REG_EAX,p)
        elif address==0x597870:
            p=word(uc,uc.reg_read(UC_X86_REG_ESP)+4);assert p in alloc and p not in freed;freed.add(p)
        elif address==0x542810:
            reach[0]+=1
        elif address==0x41dbc0:
            index=word(uc,m+0x1209d);assert index==next_unit[0]
            contribution=contributions[index]
            assert uc.reg_read(UC_X86_REG_EAX)==contribution,(spatial,index,uc.reg_read(UC_X86_REG_EAX),contribution)
            assert word(uc,m+0x120a9)==pending_total[0]
            pending_total[0]+=contribution
            for cell in selections[index]:map_values[cell]=min(255,map_values[cell]+16)
            pending[0]+=1;next_unit[0]+=1
            for i in range(count):
                expected=map_values[i]
                assert list(uc.mem_read(cells+i*0x294+0x28c,7))==[expected,expected,0,0,0,0,0]
            events.append(dict(kind='unit',index=index));round_events.append('unit')
        elif address==0x41d476 and word(uc,m+0x12099)==owner:
            # This address also follows profile exclusions; chosen active owner qualifies.
            assert pending[0]==active and next_unit[0]==active
            assert word(uc,units+0x926)==sum(contributions)==pending_total[0] and word(uc,m+0x120a9)==0
            for i in range(count):
                expected=map_values[i]
                tail=[30,20,25] if effects and (not spatial or i not in (2,3)) else [0,0,0]
                assert list(uc.mem_read(cells+i*0x294+0x24c+7*owner,7))==[expected,expected,0,*tail,0]
                for other in range(8):
                    if other!=owner:assert bytes(uc.mem_read(cells+i*0x294+0x24c+7*other,7))==bytes(7)
                assert bytes(uc.mem_read(cells+i*0x294+0x28c,7))==bytes(7)
            events.append(dict(kind='publish',units=active));round_events.append('publish')
            pending[0]=0;next_unit[0]=0;pending_total[0]=0;map_values[:]=[0]*count
    u.hook_add(UC_HOOK_CODE,hook);rounds=[]
    discarded=[]
    for invocation in range(8):
        if invocation==restart_at:
            assert pending[0]>0
            discarded.append(dict(invocation=invocation,units=pending[0],total=pending_total[0],cell_cursor=word(u,m+0x120a1)))
            put(u,m+0x12098,'B',1);pending[0]=0;next_unit[0]=0;pending_total[0]=0;map_values[:]=[0]*count
        round_events.clear();call(u,0x41d270,m,[])
        assert round_events.count('unit')<=4
        rounds.append(dict(events=list(round_events),player=word(u,m+0x12099),unit_cursor=word(u,m+0x1209d),cell_cursor=word(u,m+0x120a1),pending_units=pending[0]))
    assert sum(e['kind']=='publish' for e in events)>=2
    assert reach[0]==sum(e['kind']=='unit' for e in events)
    assert len(alloc-freed)==word(u,m+0x12094)
    return dict(active_units=active,cells=count,unit_type=kind,status=status,spatial=spatial,persistent_effects=effects,owner=owner,restart_at=restart_at,discarded=discarded,contributions=contributions,selections=selections,rounds=rounds,publications=sum(e['kind']=='publish' for e in events),native_units=sum(e['kind']=='unit' for e in events),allocated=len(alloc),freed=len(freed))

def verify():
    cases=[fixture(active,count,*mode) for active,count,mode in itertools.product((1,2,4,5,9),(4,33),((0,0),(1,0),(0,1)))]
    cases.extend(fixture(active,count,*mode,spatial) for active,count,mode,spatial in itertools.product((5,9),(4,33),((0,0),(1,0),(0,1)),('reverse','away')))
    cases.extend(fixture(5,count,kind,0,spatial,True) for count,kind,spatial in itertools.product((4,33),(0,1),(None,'reverse')))
    cases.extend(fixture(5,33,kind,0,'reverse',True,owner,restart) for kind,owner,restart in itertools.product((0,1),range(8),(None,1,2)))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
        scope='110 whole41d270 fixtures/880 calls:previous62 spatial/effect cases plus48 all8-owner first/secondpath cases with/no midcycle restart after4units orafter32of33 cell finalizations. OnlyCRTalloc/free doubled;actual greedy test/attenuation/mapgraphs/reuse/effects/publish-clear. Independent perunit contributions/all7channels/totals/4unit-32cell budgets;chosen owner map segment andother7 segments unchanged;restart discards unfinished scratch/total andretains prioralloc cleanup. Multi-active-owner relations/effectlifecycle/save/caller timing pending;type1 profile pointer synthetic,not live acceptance.')
    (ROOT/'modernization/docs/ai-danger-pipeline-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),whole_calls=sum(len(c['rounds']) for c in cases)))

if __name__=='__main__':verify()
