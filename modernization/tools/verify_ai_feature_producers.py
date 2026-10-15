"""Execute native40b420 direct-field aggregators on real nested group iterators."""
import json,struct
from unicorn.x86_const import *
from unicorn import UC_HOOK_CODE
from verify_ai_training_math import machine,put
from verify_ai_groups import group,word
from verify_ai_model_native import ROOT,SHA

FIELDS={0xe4:[100,201],0x90a:[31,53],0x90e:[41,65],0x84:[13,20],0xec:[120,200],0x88:[29,40],0xf8:[0,1],0x104:[1,0],0x912:[13,24],0x916:[21,10],0x91a:[17,23],0x8c:[0,1]}
SELECTORS=[1,2,4,5,8,10,13,14,15,16,17,18,19,21,27,28,29,30,31,32,33,34,56,57]

def run(selectors,illusion=False,side='own',rank_cutoff=0,spell_fixture=None):
    u=machine();own=0x2010000;enemy=own+0x400;vec=enemy+0x400;data=vec+0x100
    leaves=[own+0x1000+i*0x400 for i in range(2)];units=[own+0x3000+i*0x2000 for i in range(2)]
    for i,(g,unit) in enumerate(zip(leaves,units)):
        group(u,g,unit=unit,rank=i)
        put(u,unit+0xa8,'I',i)
        definition=unit+0x1000;put(u,unit+0xac,'I',definition)
        put(u,definition+0x44,'I',2 if i==0 else 0)
        if spell_fixture is not None:put(u,definition,'I',0 if i==0 else 1)
        for field,values in FIELDS.items():put(u,unit+field,'I',values[i])
        put(u,unit+0x7c,'I',int(illusion and i==1))
        for offset,value in [(0x6a6535,15+10*i),(0x6a6539,21+10*i),(0x6a6545,30+10*i),(0x6a652d,7+2*i),(0x6a6529,11+2*i)]:put(u,offset+i*0x5c9,'I',value)
    group(u,own,children=leaves if side=='own' else [])
    group(u,enemy,children=leaves if side=='enemy' else [])
    put(u,vec,'4I',0,data,data,data+1024);put(u,0x5d854c,'I',rank_cutoff)
    budget=0
    if spell_fixture is not None:
        budget=spell_fixture['budget']
        # Controlled known-spell availability/delay. Every other dependency real.
        u.mem_write(0x40a950,b'\xc2\x08\0')
        for spell in range(104):
            for category in range(18):put(u,0x6b14f1+spell*721+category*4,'i',0)
        for spell in [1,2,3,4]:
            for category in range(18):put(u,0x6b14f1+spell*721+category*4,'i',spell*(category+1) if spell!=4 else -3)
        def availability(uc,address,size,user):
            sp=uc.reg_read(UC_X86_REG_ESP);spell=word(uc,sp+4);out=word(uc,sp+8)
            put(uc,out,'I',{1:0,2:10,3:11}.get(spell,0x7fffffff))
            uc.reg_write(UC_X86_REG_EAX,int(spell in [1,2,3]))
        u.hook_add(UC_HOOK_CODE,availability,begin=0x40a950,end=0x40a950)
    sp=0x23f0000;stop=0x2000000
    put(u,sp,'I'*(6+len(selectors)),stop,own,enemy,budget,vec,len(selectors),*selectors)
    u.reg_write(UC_X86_REG_ESP,sp);u.emu_start(0x40b420,stop,count=500000)
    assert u.reg_read(UC_X86_REG_EIP)==stop
    assert word(u,vec+8)==data+4*len(selectors)
    return list(struct.unpack('<'+'i'*len(selectors),u.mem_read(data,4*len(selectors))))

def expected(illusion=False,cutoff=0,side='own'):
    ids=[i for i in range(2) if i>=cutoff]
    def total(field):return sum(FIELDS[field][i] for i in ids)
    def avg(field,half=False):return int(sum(FIELDS[field][i]//(2 if half and illusion and side=='own' and i==1 else 1) for i in ids)/len(ids)) if ids else 0
    def maxcombat(i):return max(FIELDS[0x912][i],FIELDS[0x916][i])//(2 if illusion and side=='own' and i==1 else 1)
    return {1:len(ids),2:avg(0xe4),4:avg(0x90a,True),5:avg(0x90e,True),8:avg(0x84),10:total(0xec),13:avg(0x88),14:int(sum(15+10*i for i in ids)/len(ids)) if ids else 0,15:int(sum(21+10*i for i in ids)/len(ids)) if ids else 0,16:sum(FIELDS[0xf8][i]!=0 for i in ids),17:int(sum(maxcombat(i) for i in ids)/len(ids)) if ids else 0,18:sum(FIELDS[0x104][i]!=0 for i in ids),19:int(0 in ids),21:0,27:int(sum(30+10*i for i in ids)/len(ids)) if ids else 0,28:sum(max(FIELDS[0x90a][i],FIELDS[0x90e][i])//(2 if illusion and side=='own' and i==1 else 1) for i in ids),29:sum(maxcombat(i) for i in ids),30:sum(FIELDS[0x90e][i]//(2 if illusion and side=='own' and i==1 else 1) for i in ids),31:total(0x91a),32:int(100*sum(FIELDS[0x104][i]!=0 for i in ids)/len(ids)) if ids else 0,33:int(100*sum(FIELDS[0xf8][i]!=0 for i in ids)/len(ids)) if ids else 0,34:int(sum((7+2*i)*(11+2*i) for i in ids)/len(ids)) if ids else 0,56:int(illusion and 1 in ids),57:int(100*int(illusion and 1 in ids)/len(ids)) if ids else 0}

def verify():
    cases=[]
    for side in ['own','enemy']:
        for illusion in [False,True]:
            for cutoff in [0,1,2]:
                selected=[s for s in SELECTORS if side=='own' or s<=54]
                selectors=[s+(58 if side=='enemy' else 0) for s in selected]
                actual=run(selectors,illusion,side,cutoff);want=expected(illusion,cutoff,side)
                for s,v in zip(selected,actual):
                    assert v==want[s],(side,illusion,cutoff,s,v,want[s])
                    cases.append(dict(selector=s+(58 if side=='enemy' else 0),side=side,illusion=illusion,cutoff=cutoff,value=v))
    for side in ['own','enemy']:
        for budget in [0,9,10,11]:
            selected=list(range(37,55));selectors=[s+(58 if side=='enemy' else 0) for s in selected]
            actual=run(selectors,side=side,spell_fixture=dict(budget=budget))
            admitted=sum(s for s,d in [(1,0),(2,10),(3,11)] if d<=budget)
            for category,(s,value) in enumerate(zip(selectors,actual)):
                assert value==admitted*(category+1),(side,budget,s,value)
                cases.append(dict(selector=s,side=side,budget=budget,value=value,dependency='spell availability/delay explicitly stubbed'))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Real40b420,varargs/vector insertion,recursive groups.276 direct-field cases without stubs;144 capability cases with only40a950 availability/delay stubbed. Enemy has54 group selectors; own55..58 lack mirrors. Other producers pending.')
    (ROOT/'modernization/docs/ai-feature-producer-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
