"""Native signed command-ID lookup in synthetic, balanced manager trees."""
import json
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def tree(u,manager,items,arena,nil=0x2090000):
    put(u,0x5faf50,'I',nil)
    put(u,nil,'6I',nil,nil,nil,0,0,1)
    head=arena;nodes=[arena+0x40+0x20*i for i in range(len(items))]
    items=sorted(items)
    def construct(lo,hi,parent):
        if lo==hi:return nil
        mid=(lo+hi)//2;node=nodes[mid]
        left=construct(lo,mid,node);right=construct(mid+1,hi,node)
        key,value=items[mid]
        put(u,node,'3IiII',left,parent,right,key,value,1)
        return node
    root=construct(0,len(items),head)
    put(u,head,'6I',nodes[0] if nodes else head,root,nodes[-1] if nodes else head,0,0,0)
    put(u,manager+0xbe,'I',head)
    return head

def verify():
    cases=[];manager=0x2010000
    for keys in [[],[0],[10,11],[-5,0,3,10,11,17,100,0x7fffffff]]:
        values={k:0x2030000+0x100*i for i,k in enumerate(keys)}
        u=machine();tree(u,manager,list(values.items()),0x2020000)
        before=bytes(u.mem_read(manager,0x30000))
        for query in [-0x80000000,-5,-1,0,1,2,3,9,10,11,12,16,17,18,99,100,101,0x7ffffffe,0x7fffffff]:
            actual=call(u,0x416c30,manager,[query&0xffffffff])
            assert actual==(values.get(query,0) if query>=0 else 0),(keys,query,actual)
            assert bytes(u.mem_read(manager,0x30000))==before
            cases.append(dict(keys=keys,query=query,action_pointer=actual))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
                scope='Complete416c30 and42e610 native code, no stubs or game IO. Balanced synthetic search trees verify exact match, signed negative rejection, empty/missing/extreme IDs and no mutation. Native tree insertion/deletion/red-black balancing not tested.')
    (ROOT/'modernization/docs/ai-action-lookup-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
