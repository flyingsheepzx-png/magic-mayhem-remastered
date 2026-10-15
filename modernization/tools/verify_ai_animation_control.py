"""Native animation VM control flow against independent bounded interpreter."""
import json,itertools
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def fixture(program,branch_flag=0):
    u=machine();obj=0x2010000;bank=obj+0x1000;indices=bank+0x200;records=bank+0x400
    put(u,bank+4,'II',indices,records);put(u,indices,'I',0)
    for index,(op,arg) in enumerate(program):put(u,records+44*index,'II',op,arg&0xffffffff)
    call(u,0x464c50,obj,[]);call(u,0x464ca0,obj,[bank]);call(u,0x464cb0,obj,[0,0])
    # Programs start with frame0; initialization keeps cursor on that frame.
    put(u,obj+0x20,'I',branch_flag)
    state=dict(ip=0,frame=0,active=1,delay=0,elapsed=0,loop=0,branch=branch_flag)
    trace=[]
    for tick in range(500):
        result=0
        if state['active']:
            if state['elapsed']<state['delay']:state['elapsed']+=1
            else:
                for _ in range(500):
                    op,arg=program[state['ip']];stop=False
                    if op==0:state['frame']=state['ip'];stop=True
                    elif op==1:state['delay']=arg
                    elif op==2:state['loop']=arg
                    elif op==3 and state['loop']:
                        state['loop']-=1;state['ip']+=arg-1
                    elif op==4:
                        if state['branch']:state['branch']=0
                        else:state['ip']+=arg-1
                    elif op==5:result=arg;stop=True
                    elif op==6:state['active']=0;state['frame']=None;result=1;stop=True
                    state['ip']+=1
                    if stop:break
                else:raise AssertionError('oracle instruction budget')
                state['elapsed']=0
        actual=call(u,0x464ec0,obj,[])
        assert actual==result,(program,tick,actual,result,state)
        for key,offset in [('active',8),('delay',12),('elapsed',16),('loop',20),('branch',32)]:
            assert word(u,obj+offset)==state[key],(key,tick,state)
        assert word(u,obj+24)==records+state['ip']*44
        assert word(u,obj+4)==(0 if state['frame'] is None else records+state['frame']*44)
        trace.append(actual)
        if not state['active']:break
    else:raise AssertionError('oracle step budget')
    assert call(u,0x464ec0,obj,[])==0
    return dict(program=program,branch_flag=branch_flag,trace=trace)

def initial_fixture(loop_count,event,terminal=False):
    u=machine();obj=0x2010000;bank=obj+0x1000;indices=bank+0x200;records=bank+0x400
    put(u,bank+4,'II',indices,records);put(u,indices,'I',0)
    program=[(2,loop_count),(5,event),(0,0),(6,0)] if not terminal else [(2,loop_count),(5,event),(6,0)]
    for i,(op,arg) in enumerate(program):put(u,records+i*44,'II',op,arg)
    call(u,0x464c50,obj,[]);call(u,0x464ca0,obj,[bank]);call(u,0x464cb0,obj,[0,0])
    #465000 consumes event5 and continues, unlike ordinary464ec0.
    assert word(u,obj+20)==loop_count
    assert word(u,obj+24)==records+3*44
    assert word(u,obj+8)==int(not terminal)
    assert word(u,obj+4)==(0 if terminal else records+2*44)
    result=call(u,0x464ec0,obj,[]);assert result==(0 if terminal else 1)
    return dict(kind='nonframe_initialization',loop_count=loop_count,event=event,terminal=terminal,next_result=result)

def verify():
    cases=[]
    for loops,delay in itertools.product([0,1,2,7],[0,1,4]):
        cases.append(fixture([(0,0),(1,delay),(2,loops),(0,0),(3,-1),(5,2),(6,0)]))
    for branch,delay in itertools.product([0,1,2],[0,1,4]):
        cases.append(fixture([(0,0),(1,delay),(4,2),(0,0),(5,2),(6,0)],branch))
    for loops,branch in itertools.product([0,1,3],[0,1]):
        cases.append(fixture([(0,0),(2,loops),(4,2),(0,0),(3,-2),(5,2),(6,0)],branch))
    cases.extend(initial_fixture(*v) for v in itertools.product([0,1,7],[0,2,9],[False,True]))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='27 whole464ec0 bounded-program cases plus18 nonframe initialization cases through465000,actual464c50/464ca0/464cb0,no doubles. Independent interpreter verifies every tick state for all opcodes0..6,relative loops/conditional latch/delay/events/termination. Init465000 consumes event5 until frame/end. Synthetic finite programs;fast-forward24 and actual assets pending.')
    (ROOT/'modernization/docs/ai-animation-control-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),ticks=sum(len(c.get('trace',[])) for c in cases)))

if __name__=='__main__':verify()
