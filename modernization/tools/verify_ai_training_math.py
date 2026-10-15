"""Hash-gated native quantile and symmetric-matrix inversion fixtures; no game IO."""
import json, math, struct
from pathlib import Path
from statistics import NormalDist
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *
from verify_ai_model_native import NativeScore, ROOT, SHA

native = NativeScore(ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Chaos-Wide169-engine.exe')

def machine():
    u=Uc(UC_ARCH_X86,UC_MODE_32)
    u.mem_map(0x400000,0x400000);u.mem_write(native.base,native.image)
    u.mem_map(0x2000000,0x400000)
    u.reg_write(UC_X86_REG_FPCW,0x37f)
    return u

def put(u,a,fmt,*v):u.mem_write(a,struct.pack('<'+fmt,*v))

def quantile(p):
    u=machine();sp=0x23f0000;stop=0x2000000;out=stop+32
    # Store the x87 return as double in a synthetic caller.
    u.mem_write(stop,b'\xdd\x1d'+struct.pack('<I',out)+b'\x90')
    put(u,sp,'If',stop,p);u.reg_write(UC_X86_REG_ESP,sp)
    u.emu_start(0x479f80,stop+6,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==stop+6
    return struct.unpack('<d',u.mem_read(out,8))[0]

def invert(matrix):
    n=len(matrix);u=machine();obj=0x2010000;rows=obj+32;data=rows+n*16+32
    put(u,obj,'IIII',0,rows,rows+n*16,rows+n*16)
    for i,row in enumerate(matrix):
        assert len(row)==n
        put(u,rows+i*16,'IIII',0,data+i*n*4,data+(i+1)*n*4,data+(i+1)*n*4)
        put(u,data+i*n*4,'f'*n,*row)
    sp=0x23f0000;stop=0x2000000;status=0x2020000
    put(u,sp,'III',stop,obj,status);u.reg_write(UC_X86_REG_ESP,sp)
    u.emu_start(0x47a0e0,stop,count=1000000)
    assert u.reg_read(UC_X86_REG_EIP)==stop
    code=struct.unpack('<i',u.mem_read(status,4))[0]
    flat=struct.unpack('<'+'f'*(n*n),u.mem_read(data,n*n*4))
    return code,[list(flat[i*n:(i+1)*n]) for i in range(n)]

def verify():
    cases=[]
    for p in [0.00001,0.001,0.01,0.05,0.1,0.25,0.5,0.75,0.9,0.95,0.99,0.999,0.99999]:
        actual=quantile(p);expected=NormalDist().inv_cdf(p)
        assert abs(actual-expected)<0.002,(p,actual,expected)
        cases.append(dict(kind='normal_quantile',p=p,value=actual,error=abs(actual-expected)))
    for p,expected in [(0.0,-5.0),(1.0,5.0)]:
        assert quantile(p)==expected
        cases.append(dict(kind='quantile_clamp',p=p,value=expected))
    matrices=[[[2.0]],[[2.0,0.5],[0.5,3.0]],[[4.,1.,0.5],[1.,3.,0.2],[0.5,0.2,2.]],
              [[float(6 if i==j else 0.1*(min(i,j)+1)) for j in range(5)] for i in range(5)]]
    for m in matrices:
        code,result=invert(m);assert code==0
        n=len(m);err=max(abs(sum(m[i][k]*result[k][j] for k in range(n))-(1 if i==j else 0)) for i in range(n) for j in range(n))
        assert err<0.00001,(m,result,err)
        cases.append(dict(kind='matrix_inverse',dimension=n,identity_residual=err))
    for m,expected in [([], -2),([[0.]],-1),([[-1.]],-1),([[1.,2.],[2.,1.]],-1)]:
        code,_=invert(m);assert code==expected,(m,code)
        cases.append(dict(kind='matrix_rejection',dimension=len(m),status=code))
    report=dict(engine_sha256=SHA,result='passed',cases=cases,
        constants={hex(a):native.value(a,f) for a,f in [(0x5c6008,'f'),(0x5c5f60,'i'),(0x5c5f64,'f'),(0x5c6000,'d'),(0x5c5ff4,'f'),(0x5c6070,'d')]},
        scope='Actual native 479f80 normal quantile and 47a0e0 positive-pivot symmetric matrix inverse, bounded offline emulator; not full training validation')
    (ROOT/'modernization/docs/ai-training-math-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':verify()
