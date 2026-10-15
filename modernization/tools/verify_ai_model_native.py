"""Compare recovered Python inference against actual hash-gated x86 score kernel."""
import argparse,hashlib,json,random,struct
from pathlib import Path
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
from ai_model_codec import read_models,encode_models,score
ROOT=Path(__file__).resolve().parents[2]
SHA='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'

class NativeScore:
 def __init__(self,engine):
    raw=engine.read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
    pe=pefile.PE(data=raw);self.image=pe.get_memory_mapped_image();self.base=pe.OPTIONAL_HEADER.ImageBase
    self.constants=dict(exponent_scale=self.value(0x5c5a88,'d'),cutoff=self.value(0x5c5f80,'d'),epsilon=self.value(0x5c5bb0,'f'),bin_factor=self.value(0x5c5f88,'f'))
 def value(self,a,fmt):return struct.unpack_from('<'+fmt,self.image,a-self.base)[0]
 def run(self,model,vector):
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000);u.mem_write(self.base,self.image)
    u.mem_map(0x2000000,0x400000);cursor=0x2010000
    def put(a,fmt,*v):u.mem_write(a,struct.pack('<'+fmt,*v))
    def alloc(size):
        nonlocal cursor
        p=cursor;cursor+=(size+15)&~15;return p
    n=model['dimension'];classes=model['classes'];obj=alloc(32);comp=alloc(len(classes)*40)
    put(obj,'IIII',n,0,0,comp)
    for k,c in enumerate(classes):
        f=alloc(n*48);rows=alloc(n*16+4);matrix=alloc(n*n*4)
        for i,x in enumerate(c['features']):put(f+i*48,'12f',x['threshold'],x['step'],*x['bins'])
        put(matrix,'f'*(n*n),*c['matrix'])
        for i in range(n):put(rows+4+i*16,'IIII',matrix+i*n*4,matrix+(i+1)*n*4,matrix+(i+1)*n*4,0)
        put(comp+k*40,'fIIIIIfII',c['prior'],0,f,f+n*48,f+n*48,struct.unpack('<I',struct.pack('<f',c['limit']))[0],0.0,rows,0)
    raw=alloc(16);inputs=alloc(n*4);put(inputs,'i'*n,*vector);put(raw,'IIII',n,inputs,inputs+n*4,inputs+n*4)
    scratch=alloc(n*4);output=alloc(len(classes)*4);sp=0x23f0000
    put(sp+0x14,'I',obj);put(sp+0x2c,'I',scratch)
    put(sp+0xe4,'III',raw,len(classes),output)
    u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EAX,obj);u.reg_write(UC_X86_REG_ESI,len(classes));u.reg_write(UC_X86_REG_FPCW,0x37f)
    u.emu_start(0x4768f7,0x476b10,count=3000000)
    if u.reg_read(UC_X86_REG_EIP)!=0x476b10:raise RuntimeError('kernel did not finish')
    return list(struct.unpack('<'+'f'*len(classes),u.mem_read(output,4*len(classes))))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--brain',type=Path,default=Path('D:/Games/Magic&Mayham_Remastered_1.1/runtime/AI/Brain.dat'));p.add_argument('--output',type=Path);a=p.parse_args()
 decoded=read_models(a.brain);assert hashlib.sha256(encode_models(decoded)).hexdigest()==decoded['sha256']
 native=NativeScore(ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Chaos-Wide169-engine.exe');rng=random.Random(11);cases=0;error=0.0
 for model in decoded['models']:
    for kind in range(4):
        vector=[0]*model['dimension'] if kind==0 else [rng.randint(-100,100) for _ in range(model['dimension'])] if kind==1 else [int(f['threshold']+f['step']*(0.45 if kind==2 else -0.45)) for f in model['classes'][0]['features']]
        expected=score(model,vector,**native.constants);actual=native.run(model,vector)
        delta=max(abs(x-y) for x,y in zip(expected,actual));assert delta<0.00003,(model['action_id'],kind,expected,actual,delta)
        error=max(error,delta);cases+=1
 report=dict(result='passed',cases=cases,max_probability_error=error,engine_sha256=SHA,brain_sha256=decoded['sha256'],constants=native.constants,scope='lossless Brain roundtrip and native x86 kernel normalization/bin selection/quadratic score/exponent/probability comparison; no game launched')
 if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,indent=2))
