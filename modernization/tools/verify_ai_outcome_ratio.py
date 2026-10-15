"""Whole native40a3b0 outcome ratio and real466870 lookup; no doubles."""
import itertools,json,struct
from fractions import Fraction
from unicorn.x86_const import *
from verify_ai_retirement import setup,f32
from verify_ai_resource_value import ext
from verify_ai_training_math import native,put
from verify_ai_model_native import ROOT,SHA

def expected_ratio(baseline,current,safety,gains,losses,missing=False):
    eps=Fraction(native.value(0x5c5378,'d'))
    metric=Fraction(0) if missing else ext(Fraction(current,safety+1))
    benefit=ext(Fraction(gains+1,losses+1))
    numerator=ext(ext(Fraction(f32(baseline))+eps)*benefit)
    return float(ext(numerator/ext(metric+eps)))

def fixture(baseline,current,safety,gains,losses,missing):
    u,a,*_=setup(baseline,current,safety,gains,losses,missing)
    stop=0x2001000;out=stop+32;sp=0x23f0000
    u.mem_write(stop,b'\xdd\x1d'+struct.pack('<I',out)+b'\x90')
    put(u,sp,'I',stop);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,a)
    u.emu_start(0x40a3b0,stop+6,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==stop+6
    result=struct.unpack('<d',u.mem_read(out,8))[0]
    expected=expected_ratio(baseline,current,safety,gains,losses,missing)
    assert result==expected,(baseline,current,safety,gains,losses,missing,result,expected)
    return dict(baseline=baseline,current=current,safety=safety,gains=gains,losses=losses,missing=missing,ratio=result)

def verify():
    cases=[fixture(*v) for v in itertools.product([0.,.05,.1,1.], [0,1,100,1000], [0,99,999], [0,3,10000], [0,3,10000], [False,True])]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Whole40a3b0 with real466870, no function doubles; f32 baseline and exact x87 extended intermediates, stored double return. Nonnegative counters; signed overflow, singular denominator and producer semantics remain pending.')
    (ROOT/'modernization/docs/ai-outcome-ratio-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
