"""Whole466980 active-profile/relation-byte existence predicate, no doubles."""
import itertools,json
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA

def fixture(owner,mask,role,relation):
    u=machine();base=0x643a80
    for slot in range(8):
        put(u,base+slot*0x154,'II',bool(mask&(1<<slot)),role)
        put(u,base+slot*0x154+0x18+owner,'B',relation)
    actual=call(u,0x466980,base,[owner])
    expected=int(bool(mask) and role!=0 and relation==0)
    assert actual==expected,(owner,mask,role,relation,actual,expected)
    return dict(owner=owner,active_mask=mask,role=role,relation=relation,result=actual)

def verify():
    cases=[fixture(*v) for v in itertools.product(range(8),[0,1,2,4,8,16,32,64,128,255],[0,1,2,0xffffffff],[0,1,2,255])]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Whole466980 no doubles. Exists slot0..7 with profile+0 nonzero,+4 nonzero and byte+18+owner equal0. Meaning of+4/profile producer and relationship matrix initialization still pending; no self exclusion beyond table contents.')
    (ROOT/'modernization/docs/ai-opponent-predicate-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
