"""Native effect directory printer/Data1 assignment, explicit Win32 input."""
import configparser,hashlib,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine,put
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA
from inspect_ai_animation_assets import RUNTIME

PRINTERS={'normal':31,'transparent':2,'transparent25':3,'transparent50':4,'transparent75':5}

def fixture(printer,data):
    u=machine();entry=0x2010000;api=entry+0x1000;sp=0x23f0000
    u.mem_write(entry,b'\xa5'*16);put(u,0x6fa2e8,'I',0);u.mem_write(api,b'\xc2\x18\x00');seen=[]
    def capture(uc,address,size,user):
        if address!=api:return
        args=struct.unpack('<6I',uc.mem_read(uc.reg_read(UC_X86_REG_ESP)+4,24))
        assert args[0]==0x5fe76c and args[2:]==(0x5faf28,0x5fe018,256,0x5fe66c)
        value=printer if args[1]==0x5e0274 else data
        assert args[1] in (0x5e0274,0x5e0228);seen.append(args[1])
        uc.mem_write(0x5fe018,value.encode()+b'\0');uc.reg_write(UC_X86_REG_EAX,len(value))
    u.hook_add(UC_HOOK_CODE,capture)
    u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EBP,api);u.reg_write(UC_X86_REG_ESI,entry+8)
    u.emu_start(0x49c9aa,0x49ca92,count=100000)
    assert u.reg_read(UC_X86_REG_EIP)==0x49ca92 and seen==[0x5e0274,0x5e0228]
    expected_printer=PRINTERS.get(printer.lower(),0xa5a5a5a5)
    expected_data=int(data) if data and data!='invalid' else 0 if data else 0xa5a5a5a5
    assert word(u,entry+8)==expected_printer and word(u,entry+12)==expected_data&0xffffffff
    assert bytes(u.mem_read(entry,8))==b'\xa5'*8
    return dict(printer_text=printer,data_text=data,printer_value=word(u,entry+8),data_value=word(u,entry+12))

def verify():
    path=RUNTIME/'CFG/effectani.cfg';raw=path.read_bytes();text=raw.decode('latin1');text=text[text.index('[HEADER]'):]
    cfg=configparser.ConfigParser(inline_comment_prefixes=(';',),strict=False);cfg.read_string(text)
    count=int(cfg['HEADER']['NumberofAnimations']);cases=[]
    for i in range(count):
        section=cfg[f'ANI_{i}'];case=fixture(section.get('SpritePrinter',''),section.get('Data1',''));case['directory_index']=i;cases.append(case)
    cases.extend(fixture(printer,data) for printer in ('NORMAL','transparent','TrAnSpArEnT25','TRANSPARENT50','TRANSPARENT75','bad','','NORMALsuffix') for data in ('','0','-1','99','invalid'))
    assert path.read_bytes()==raw
    report=dict(result='passed',engine_sha256=SHA,config_sha256=hashlib.sha256(raw).hexdigest(),cases=cases,scope='Native49c9aa..49ca92 directory entry8 printer/entryc Data1 assignment;real59db40(C-locale)/59c5a4,Win32 API doubled. All222 installed entries and40 edges. Missing/unrecognized printer preserves prior;nonempty invalid Data1 parses0,empty preserves. Renderer and whole config loader integration pending.')
    (ROOT/'modernization/docs/ai-effect-render-fields-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases)))

if __name__=='__main__':verify()
