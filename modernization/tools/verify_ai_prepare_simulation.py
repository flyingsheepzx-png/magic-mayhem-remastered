"""Mode0 prepare duration through real animation interpreter, bounded programs."""
import itertools,json
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA
from verify_ai_registration_lifecycle import MODE_FIELDS

OFFSETS={21:0x4a0,39:0x220,44:0x460,52:0x490}

def fixture(row,delay,action_delay,program_kind):
    u=machine();a=0x2010000;directory=0x2020000;definitions=0x2030000
    bank=0x2040000;indices=bank+0x400;records=bank+0x800;obj=0x2050000
    action=row['action_id'];offset=OFFSETS[action]
    put(u,MODE_FIELDS[action],'I',0)
    put(u,0x6898d0,'I',directory);put(u,0x6894a0,'I',definitions)
    put(u,directory+offset,'II',0,0)
    put(u,definitions+4,'II',indices,records);put(u,indices,'I',0)
    put(u,a+0x14e,'I',action_delay);put(u,a+0x162,'B',1)
    program=[(0,0),(1,delay),(0,0),(6,0)] if program_kind==0 else [(0,0),(1,delay),(5,2),(6,0)]
    for index,(op,arg) in enumerate(program):put(u,records+index*44,'II',op,arg)
    # Independently step actual VM first, including initialization.
    call(u,0x464c50,obj,[]);call(u,0x464ca0,obj,[definitions]);call(u,0x464cb0,obj,[0,0])
    results=[]
    for _ in range(delay+10):
        result=call(u,0x464ec0,obj,[]);results.append(result)
        if result:break
    expected_steps=delay+3 if program_kind==0 else 2
    assert len(results)==expected_steps and results[-1]==(1 if program_kind==0 else 2),(delay,program_kind,results)
    duration=call(u,int(row['methods']['prepare_execute'],16),a,[])
    expected=action_delay+(8 if action==39 else 5)+expected_steps
    assert duration==expected and bytes(u.mem_read(a+0x162,1))==b'\0'
    return dict(action_id=action,delay=delay,action_delay=action_delay,program_kind=program_kind,vm_results=results,duration=duration)

def verify():
    rows=json.loads((ROOT/'modernization/docs/ai-action-registry.json').read_text())['actions']
    cases=[fixture(row,*v) for row in rows if row['action_id'] in OFFSETS
           for v in itertools.product([0,1,5,30],[0,7,40],[0,1])]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Four whole prepare mode0 methods with actual464c50/464ca0/464cb0/464ec0 and actual VM step calls,no doubles. Synthetic opcode0/1/5/6 programs; stops first nonzero event,not necessarily animation end. Loop/jump opcodes2/3/4,fast-forward mode,real assets/directory loading and invalid modes pending.')
    (ROOT/'modernization/docs/ai-prepare-simulation-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
