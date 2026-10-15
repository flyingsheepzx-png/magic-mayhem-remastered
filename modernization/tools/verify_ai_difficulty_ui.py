"""Whole4b3420 difficulty propagation with explicit external menu sinks."""
import itertools,json
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def fixture(page,event,index,difficulty):
    u=machine();menu=0x2010000;items=menu+0x400;records=menu+0x800
    put(u,menu+0x7c,'i',page);put(u,menu+0x5f,'III',items,index,4)
    for n in range(4):
        p=records+n*128;put(u,items+4*n,'I',p);put(u,p+0x2d,'I',difficulty if n==index else 99)
    put(u,0x689924,'I',77)
    for entry,result in [(0x54eec0,0),(0x557510,0),(0x4bfb10,5),(0x5908e0,0),(0x594230,100)]:
        u.mem_write(entry,b'\xb8'+result.to_bytes(4,'little')+(b'\xc2\x04\x00' if entry==0x594230 else b'\xc3'))
    call(u,0x4b3420,menu,[event])
    expected=(difficulty if event==4 or page!=22 else 0) if event in (0,2,3,4) else 77
    assert word(u,0x689924)==expected,(page,event,index,difficulty,word(u,0x689924),expected)
    return dict(page=page,event=event,index=index,difficulty=difficulty,result=expected)

def verify():
    cases=[fixture(*v) for v in itertools.product([3,4,22],[0,2,3,4,5],range(4),range(4))]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Whole4b3420 menu dispatcher with native item lookup/difficulty propagation; five external menu/campaign helpers explicit constant-return doubles. Numeric page/event meanings and menu item labels unresolved; player files untouched.')
    (ROOT/'modernization/docs/ai-difficulty-ui-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
