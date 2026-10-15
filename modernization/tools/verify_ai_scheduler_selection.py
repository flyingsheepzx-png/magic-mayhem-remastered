"""Native scheduler candidate selection slice, explicit RNG/commit doubles."""
import itertools,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def fixture(score,best,ties,rng,commit,weighted,skip_one,offset=0.,weight_sum=0.):
    u=machine();m=0x2010000;frame=0x2040000;slot=0x2050000;a=slot+0x100;vtable=a+0x100
    put(u,frame+8,'f',score);put(u,frame+0x10,'f',offset)
    put(u,frame+0x18,'B',commit);put(u,frame+0x1c,'B',skip_one)
    put(u,frame-8,'I',slot);put(u,slot,'I',a);put(u,a,'I',vtable)
    put(u,vtable+12,'I',0x2060000);u.mem_write(0x2060000,b'\xc3')
    put(u,m+0x11ddc,'B',weighted);put(u,m+0x11ddd,'f',best)
    put(u,m+0x11de1,'I',ties);put(u,m+0x11fe9,'f',weight_sum)
    u.mem_write(0x54e200,b'\xb8'+struct.pack('<I',rng)+b'\xc3')
    hits=[]
    def inspect(uc,address,size,user):
        if address==0x2060000:hits.append(uc.reg_read(UC_X86_REG_ECX))
    u.hook_add(UC_HOOK_CODE,inspect)
    u.reg_write(UC_X86_REG_ESI,m);u.reg_write(UC_X86_REG_EBP,frame)
    u.reg_write(UC_X86_REG_ESP,0x23f0000)
    u.emu_start(0x428751,0x4288be,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==0x4288be
    skipped=skip_one and score==1.
    adjusted=f32(score+offset)
    expected_best=best;expected_ties=ties;expected_sum=weight_sum;selected=False
    if not skipped:
        if not weighted or adjusted==1. or best==1.:
            if adjusted>=best:
                expected_ties=(0 if adjusted>best else ties)+1
                if (rng&0x7fffffff)%expected_ties==0:
                    expected_best=adjusted;selected=bool(commit)
        else:
            weight=1. if adjusted>-1. else 0.
            expected_sum=f32(weight_sum+weight)
            wins=expected_sum==0. or (rng&0x7fffffff)*2**-31<weight/expected_sum
            selected=wins and commit
            if selected:expected_best=max(best,adjusted)
    assert struct.unpack('<f',u.mem_read(m+0x11ddd,4))[0]==expected_best
    assert word(u,m+0x11de1)==expected_ties
    assert struct.unpack('<f',u.mem_read(m+0x11fe9,4))[0]==expected_sum
    assert hits==([a] if selected else [])
    assert word(u,m+0x11fe5)==(slot if selected else 0)
    assert bytes(u.mem_read(frame-1,1))[0]==int(selected)
    return dict(score=score,best=best,ties=ties,rng=rng,commit=commit,
                weighted=weighted,skip_one=skip_one,offset=offset,weight_sum=weight_sum,
                selected=selected,result_best=expected_best,result_ties=expected_ties,result_sum=expected_sum)

def verify():
    cases=[fixture(*v) for v in itertools.product([-1.,-.5,0.,.5,1.],[-1.,0.,.5,1.],
            [0,2],[0,1,0x7fffffff],[False,True],[False,True],[False,True])]
    cases.extend(fixture(score,0.,2,rng,commit,True,False,offset,total)
                 for score,offset,total,rng,commit in itertools.product([-1.,-.5,.5],[-.5,.5],
                    [1.,4.],[0,0x40000000,0x7fffffff],[False,True]))
    report=dict(result='passed',engine_sha256=SHA,cases=cases,
                scope='Exact428751..4288be native selection, real x87 comparisons/state updates; RNG54e200 fixed and action commit callback captured. Covers max/tie reservoir and alternate binary-weight reservoir,score1 skip/priority,offset and disabled commit. Full evaluator/scheduler continuation,production RNG and NaN inputs pending.')
    (ROOT/'modernization/docs/ai-scheduler-selection-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
