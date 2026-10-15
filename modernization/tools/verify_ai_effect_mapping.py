"""Native effect config numeric/file mapping slice; Win32 text input doubled."""
import configparser,hashlib,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA
from inspect_ai_animation_assets import RUNTIME

def fixture(animation,file_ref,file_count=13):
    u=machine();sp=0x23f0000;entry=0x2010000;api=entry+0x1000
    u.mem_write(entry,b'\xa5'*16);put(u,sp+0x14,'I',entry+8);put(u,sp+0x18,'i',file_count)
    put(u,0x6fa2e8,'I',0);u.mem_write(0x5fe018,animation.encode()+b'\0')
    u.mem_write(api,b'\xc2\x18\x00');calls=[]
    def capture(uc,address,size,user):
        if address!=api:return
        args=struct.unpack('<6I',uc.mem_read(uc.reg_read(UC_X86_REG_ESP)+4,24))
        assert args==(0x5fe76c,0x5e028c,0x5faf28,0x5fe018,256,0x5fe66c)
        data=file_ref.encode();uc.mem_write(0x5fe018,data+b'\0');uc.reg_write(UC_X86_REG_EAX,len(data));calls.append(1)
    u.hook_add(UC_HOOK_CODE,capture);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EBP,api)
    u.reg_write(UC_X86_REG_EAX,len(animation))
    u.emu_start(0x49c8c3,0x49c9aa,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==0x49c9aa and len(calls)==1
    expected=int(animation) if animation else 0xa5a5a5a5
    expected_file=next((i for i in range(max(file_count,0)) if file_ref.lower()==f'effects{i}'),0xa5a5a5a5)
    assert word(u,entry)==expected&0xffffffff and word(u,entry+4)==expected_file
    assert bytes(u.mem_read(entry+8,8))==b'\xa5'*8
    return dict(animation_text=animation,file_ref=file_ref,file_count=file_count,animation_value=word(u,entry),bank_index=word(u,entry+4))

def verify():
    path=RUNTIME/'CFG/effectani.cfg';raw=path.read_bytes();text=raw.decode('latin1');text=text[text.index('[HEADER]'):]
    cfg=configparser.ConfigParser(inline_comment_prefixes=(';',),strict=False);cfg.read_string(text)
    count=int(cfg['HEADER']['NumberofAnimations']);files=int(cfg['HEADER']['NumberOfEffectsFile'])
    cases=[]
    for i in range(count):
        section=cfg[f'ANI_{i}'];case=fixture(section.get('AnimationNo',''),section.get('AnimationFileRef',''),files)
        case['directory_index']=i;cases.append(case)
    cases.extend(fixture(anim,ref,n) for anim in ('','-1','0','101') for ref in ('effects0','EfFeCtS12','EFFECTS13','bad','') for n in (0,1,13))
    assert path.read_bytes()==raw
    report=dict(result='passed',engine_sha256=SHA,config_sha256=hashlib.sha256(raw).hexdigest(),cases=cases,scope='Native49c8c3..49c9aa numeric assignment/file index mapping. AnimationNo API return/text supplied directly; AnimationFileRef Win32 API explicit double. Real59c5a4/59de2f/59db40(C-locale),all222 installed entries plus60 edge combinations. Writes entry0 animation,entry4 bank,index loop0..file_count-1; missing/unmatched leaves prior. Whole config loader,printer/data fields/OS IO pending.')
    (ROOT/'modernization/docs/ai-effect-mapping-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),installed_entries=count))

if __name__=='__main__':verify()
