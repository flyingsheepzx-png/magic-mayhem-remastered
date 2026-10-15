"""Fast animation mode against explicit forward replay, native helpers unchanged."""
import itertools,json
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def fixture(delay,loops,event,negative_jump=False):
    u=machine();fast=0x2010000;plain=fast+0x100;bank=fast+0x1000;indices=bank+0x200;records=bank+0x400
    put(u,bank+4,'II',indices,records);put(u,indices,'I',0)
    program=[(0,0),(1,delay),(2,loops),(0,0),(3,-1),(5,event),(6,0)]
    if negative_jump:program=[(0,0),(1,delay),(0,0),(4,-1),(6,0)]
    for i,(op,arg) in enumerate(program):put(u,records+i*44,'II',op,arg&0xffffffff)
    for obj in (fast,plain):
        call(u,0x464c50,obj,[]);call(u,0x464ca0,obj,[bank])
    call(u,0x464cb0,plain,[0,0])
    steps=0
    while True:
        cursor=word(u,plain+24);op=word(u,cursor);arg=word(u,cursor+4)
        result=call(u,0x464ec0,plain,[]);steps+=1
        if result==2 or word(u,plain+8)==0 or (op==4 and arg&0x80000000):break
        assert steps<500
    call(u,0x464cb0,fast,[0,1])
    assert word(u,fast+0x2c)==steps and word(u,fast+0x28)==steps-1
    counter=steps-1;trace=[]
    for tick in range(steps+2):
        if word(u,fast+8)==0:
            assert call(u,0x464ec0,fast,[])==0;break
        counter=counter-1 if counter else steps
        call(u,0x464cb0,plain,[0,0])
        expected=0
        for _ in range(counter):expected=call(u,0x464ec0,plain,[])
        actual=call(u,0x464ec0,fast,[])
        assert actual==expected and word(u,fast+0x28)==counter
        assert word(u,fast+0x24)==1 and word(u,fast+0x2c)==steps
        for offset in (0,4,8,12,16,20,24,28,32):
            assert word(u,fast+offset)==word(u,plain+offset),(delay,loops,event,tick,offset)
        trace.append(dict(counter=counter,result=actual))
    return dict(delay=delay,loops=loops,event=event,negative_jump=negative_jump,total_steps=steps,replay_trace=trace)

def verify():
    cases=[fixture(*v) for v in itertools.product([0,1,4],[0,1,3],[0,2,9])]
    cases.extend(fixture(delay,0,0,True) for delay in [0,1,4])
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Whole464cb0 fast initialization and464ec0 fast branch through real464d70 reset/recursive replay; no doubles. Compared to explicit repeated native ordinary stepping for bounded synthetic delay/loop/event/end programs and negative opcode4 scan boundary. Differential test shares normal VM,independently verified in animation-control report. Actual assets/unbounded malformed programs excluded.')
    (ROOT/'modernization/docs/ai-animation-replay-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
