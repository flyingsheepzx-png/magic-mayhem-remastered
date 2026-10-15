"""Native registration-state suffix, excludes tree insert/group/factory calls."""
import itertools,json,struct
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_retirement import f32
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

def fixture(mode,score,tick,duration,serial,current,safety,missing):
    u=machine();m=0x2010000;a=0x2040000;slot=a+0x800;wizard=a+0x1000
    u.mem_write(a,b'\xa5'*0x80)
    put(u,m+0x11fe5,'I',slot);put(u,slot,'I',a)
    put(u,m+0x14,'I',tick);put(u,m+0x11ddc,'B',mode)
    put(u,m+0x11ddd,'f',score);put(u,m+0xca,'I',serial)
    put(u,wizard+0x922,'ii',current,safety)
    u.reg_write(UC_X86_REG_EAX,0 if missing else wizard)
    u.reg_write(UC_X86_REG_EBX,duration);u.reg_write(UC_X86_REG_EDI,2)
    u.reg_write(UC_X86_REG_ESI,m);u.reg_write(UC_X86_REG_ESP,0x23f0000)
    u.emu_start(0x428a5c,0x428b25,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==0x428b25
    assert word(u,a+0xc)==tick and word(u,a+0x10)==(tick+duration)&0xffffffff
    assert bytes(u.mem_read(a+0x14,2))==b'\0\0'
    assert bytes(u.mem_read(a+0x1a,1))==bytes([mode])
    assert struct.unpack('<f',u.mem_read(a+0x1b,4))[0]==f32(score)
    assert word(u,a+0x1f)==serial and word(u,a+0x27)==2
    baseline=struct.unpack('<f',u.mem_read(a+0x2b,4))[0]
    assert baseline==(0. if missing else f32(current/(safety+1)))
    assert word(u,a+0x2f)==word(u,a+0x33)==0
    assert word(u,m+0xca)==(serial+1)&0xffffffff and word(u,slot)==a
    assert word(u,a+0x23)==0xa5a5a5a5
    return dict(mode=mode,score=score,tick=tick,duration=duration,serial=serial,current=current,safety=safety,missing=missing,baseline=baseline)

def verify():
    cases=[fixture(*v) for v in itertools.product([0,1,2],[-1.,.5,1.],[100,0xfffffff0],[0,8,40],[0,0xffffffff],[0,100],[0,999],[False,True])]
    report=dict(result='passed',engine_sha256=SHA,cases=cases,scope='Native428a5c..428b25 registration state writes only; no function doubles. Explicit owner/wizard/duration register inputs. Tree insertion, group ownership, prepare callback, wizard lookup and post-state fresh factory excluded; modes other than0/1 synthetic.')
    (ROOT/'modernization/docs/ai-registration-state-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
