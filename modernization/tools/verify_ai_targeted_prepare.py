"""Whole eight targeted-spell prepare functions, geometry path only."""
import itertools,json
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_registration_lifecycle import SPELL_IDS,MODE_FIELDS
from verify_ai_model_native import ROOT,SHA

def fixture(row,difference,global_step,global_delay,action_delay):
    u=machine();a=0x2010000;target=a+0x1000;definition=target+0x1000
    action=row['action_id']
    if action in MODE_FIELDS:put(u,MODE_FIELDS[action],'I',3)
    put(u,target+0xac,'I',definition);put(u,definition+0x19c,'I',difference+20)
    put(u,target+0x1c,'I',20);put(u,a+0x15e,'I',target)
    put(u,a+0x14e,'I',action_delay);put(u,a+0x162,'B',1)
    put(u,0x6c549c,'I',global_step);put(u,0x5e147c,'I',global_delay)
    actual=call(u,int(row['methods']['prepare_execute'],16),a,[])
    expected=(difference+global_step*16)//12+global_delay//2+action_delay+(8 if action==39 else 5)
    assert actual==expected and bytes(u.mem_read(a+0x162,1))==b'\0'
    assert word(u,a+0x15e)==target and word(u,a+0x14e)==action_delay
    return dict(action_id=action,difference=difference,global_step=global_step,global_delay=global_delay,action_delay=action_delay,duration=actual)

def verify():
    rows=json.loads((ROOT/'modernization/docs/ai-action-registry.json').read_text())['actions']
    cases=[fixture(row,*v) for row in rows if row['action_id'] in SPELL_IDS
           for v in itertools.product([0,12,120],[0,2,10],[0,3,10],[0,5,40])]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Whole eight prepare methods,mode3 for conditional branches; actual464c50 where called,no doubles. Nonnegative geometry/global-delay fixtures; mode0 simulation,other globals,overflow/signed-negative inputs and field producers not covered.')
    (ROOT/'modernization/docs/ai-targeted-prepare-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
