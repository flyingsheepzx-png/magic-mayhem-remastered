"""Native nonfatal damage and source/victim action attribution."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA
from verify_ai_action_lookup import tree

def verify():
    cases=[]
    for kind,depth,shared,source in itertools.product([0,1,24],[0,2],[False,True],[False,True]):
        u=machine();unit=0x2010000;definition=unit+0x2000;payload=definition+0x1000
        actions=[payload+0x1000+i*0x200 for i in range(4)]
        put(u,unit+0xac,'I',definition);put(u,definition,'I',kind)
        put(u,unit+0xa8,'I',1);put(u,unit+0xe4,'I',100);put(u,unit+0x174,'I',2)
        put(u,unit+0x660,'I',1);put(u,0x6a5f98,'I',100)
        d=0x6a5f80+0x5c9;put(u,d,'I',kind);put(u,d+0x18,'I',100);put(u,d+0x58,'I',1)
        for i in range(28):put(u,d+0x1a0+4*i,'I',20);put(u,d+0x280+4*i,'I',36)
        for slot in range(2):
            g=payload+0x200+slot*0x400
            put(u,unit+0x678+4*slot,'I',g)
            for n in range(depth):put(u,g+n*0x100+0x39,'I',g+(n+1)*0x100)
            put(u,g+depth*0x100+5,'I',actions[2 if shared else 2+slot])
        put(u,payload,'II',10,11)
        # Use real manager lookup and lower_bound, not a command-ID test double.
        tree(u,0x690600,[(10,actions[0])],0x2070000)
        tree(u,0x644550,[(11,actions[1])],0x2080000)
        values=[]
        def hook(uc,address,size,user):
            if address==0x514b5b:values.append(uc.reg_read(UC_X86_REG_EAX))
        u.hook_add(UC_HOOK_CODE,hook)
        result=call(u,0x514990,unit,[10,payload if source else 0])
        assert result==1 and word(u,unit+0xe4)==90 and len(values)==1
        value=values[0];assert value>0
        for i,a in enumerate(actions):
            assert word(u,a+0x2f)==(value*(2 if kind in [0,24] else 1) if source and i<2 else 0)
            expected=value*(2 if shared else 1) if i==2 else value if i==3 and not shared else 0
            assert word(u,a+0x33)==expected
        cases.append(dict(unit_type=kind,parent_depth=depth,shared_victim_action=shared,source_command_present=source,value=value,health_after=90))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Full nonfatal514990 with real416d80/505c50/505bf0/416c30/42e610, no stubs. Synthetic manager trees and membership hierarchies; local UI warning excluded by unit660. Real ancestor propagation and both victim slots; fatal death path untested.')
    (ROOT/'modernization/docs/ai-damage-attribution-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
