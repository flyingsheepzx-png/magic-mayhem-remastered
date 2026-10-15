"""Whole49c5b0 with native array construction, mapping and ANI loading.

Win32 profile/cwd, CRT allocation/file IO and sprite resource boundary doubles.
No game process, disk modification or behavioral patch.
"""
import configparser, hashlib, json, struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_ai_training_math import machine, put
from verify_ai_groups import word
from verify_ai_model_native import ROOT, SHA
from inspect_ai_animation_assets import RUNTIME
from verify_ai_action_primitives import call
from verify_ai_prepare_simulation import OFFSETS
from verify_ai_registration_lifecycle import MODE_FIELDS

def cstr(u,p):
    data=bytearray()
    while True:
        b=bytes(u.mem_read(p+len(data),1))
        if b==b'\0':return data.decode('latin1')
        data.extend(b)
        assert len(data)<1024

def fixture(cfg, fail_sprite=None, fail_ani=None):
    u=machine();u.mem_map(0,4096);obj=0x2010000;sp=0x23f0000;stop=0x2000000
    cwd_api=0x2020000;profile_api=cwd_api+16
    put(u,0x5c50bc,'I',cwd_api);put(u,0x5c507c,'I',profile_api)
    u.mem_write(cwd_api,b'\xc2\x08\x00');u.mem_write(profile_api,b'\xc2\x18\x00')
    put(u,0x6fa2e8,'I',0)
    allocations={};bump=[0x2100000];handles={};opens=[];closes=[];profile=[];sprites=[]
    entries={0x597850:0,0x597870:0,0x597880:0,0x5979b0:0,
             0x57d310:8,0x57d690:8,0x4a1120:0,0x59c359:0,
             0x59c4c3:0,0x5b74d8:0,0x59d9eb:0}
    for p,n in entries.items():u.mem_write(p,b'\xc2'+struct.pack('<H',n) if n else b'\xc3')
    def inspect(uc,address,size,user):
        if address not in entries and address not in (cwd_api,profile_api):return
        s=uc.reg_read(UC_X86_REG_ESP)
        if address==cwd_api:
            n,out=struct.unpack('<2I',uc.mem_read(s+4,8));assert n==256
            uc.mem_write(out,b'X:\\isolated\0');uc.reg_write(UC_X86_REG_EAX,11)
        elif address==profile_api:
            section,key,default,out,n,path=struct.unpack('<6I',uc.mem_read(s+4,24))
            sec=cstr(uc,section);key=cstr(uc,key);assert cstr(uc,path).lower()=='x:\\isolated\\cfg\\effectani.cfg'
            value=cfg[sec].get(key,cstr(uc,default)) if sec in cfg else cstr(uc,default)
            data=value.encode('latin1')[:n-1];uc.mem_write(out,data+b'\0');uc.reg_write(UC_X86_REG_EAX,len(data));profile.append((sec,key))
        elif address in (0x597850,0x597880):
            n=word(uc,s+4);p=bump[0];bump[0]+=(n+15)&~15;assert bump[0]<0x23d0000
            allocations[p]=n;uc.mem_write(p,b'\xa5'*n);uc.reg_write(UC_X86_REG_EAX,p)
        elif address in (0x597870,0x5979b0):
            assert word(uc,s+4) in allocations
        elif address==0x57d310:
            name=cstr(uc,word(uc,s+4));assert word(uc,s+8)==16
            index=len(sprites);assert name.lower()==f'sprites\\effects{index}.spr'
            sprites.append(name);uc.reg_write(UC_X86_REG_EAX,0 if index==fail_sprite else 0x2030000)
        elif address==0x57d690:
            assert tuple(struct.unpack('<2I',uc.mem_read(s+4,8)))==(1,16)
            assert uc.reg_read(UC_X86_REG_ECX)==word(uc,0x6de4dc)+(len(sprites)-1)*36
        elif address==0x4a1120:
            name=cstr(uc,uc.reg_read(UC_X86_REG_ECX));index=len(opens)
            assert name.lower()==f'sprites\\effects{index}.ani';opens.append(name)
            if index==fail_ani:uc.reg_write(UC_X86_REG_EAX,0)
            else:
                h=77+index;handles[h]=[(RUNTIME/'Sprites'/f'EFFECTS{index}.ANI').read_bytes(),0]
                uc.reg_write(UC_X86_REG_EAX,h)
        elif address==0x59c359:
            out,unit,count,h=struct.unpack('<4I',uc.mem_read(s+4,16));raw,pos=handles[h]
            data=raw[pos:pos+unit*count];uc.mem_write(out,data);handles[h][1]+=len(data);uc.reg_write(UC_X86_REG_EAX,len(data)//unit)
        elif address==0x59c4c3:
            h=word(uc,s+4);assert handles[h][1]==len(handles[h][0]);closes.append(h);uc.reg_write(UC_X86_REG_EAX,0)
        elif address==0x5b74d8:uc.reg_write(UC_X86_REG_EAX,word(uc,s+4))
        elif address==0x59d9eb:uc.reg_write(UC_X86_REG_EAX,len(handles[word(uc,s+4)][0]))
    u.hook_add(UC_HOOK_CODE,inspect)
    put(u,sp,'I',stop);u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,obj)
    u.emu_start(0x49c5b0,stop,count=5000000)
    assert u.reg_read(UC_X86_REG_EIP)==stop,hex(u.reg_read(UC_X86_REG_EIP))
    result=u.reg_read(UC_X86_REG_EAX);assert result==int(fail_sprite is None and fail_ani is None)
    count=int(cfg['HEADER']['NumberofAnimations']);files=max(1,int(cfg['HEADER']['NumberOfEffectsFile']))
    assert len(profile)==2+count*4 and word(u,0x5fed74)==files
    directory=word(u,obj+0x438);bank=word(u,obj+8);sprite=word(u,0x6de4dc)
    assert allocations[directory]==count*16
    assert word(u,bank-4)==word(u,sprite-4)==files
    printers={'normal':31,'transparent':2,'transparent25':3,'transparent50':4,'transparent75':5}
    for i in range(count):
        sec=cfg[f'ANI_{i}'];actual=struct.unpack('<4I',u.mem_read(directory+16*i,16))
        expected=(int(sec['AnimationNo']),int(sec['AnimationFileRef'][7:]),printers[sec['SpritePrinter'].lower()],int(sec['Data1'])&0xffffffff)
        assert actual==expected,(i,actual,expected)
    loaded=files if result else (fail_sprite if fail_sprite is not None else fail_ani)
    assert len(closes)==loaded
    for i in range(files):
        b=bank+i*0x114
        assert word(u,b+0xc)==0
        if i< len(sprites)-(fail_sprite is not None):
            assert word(u,b+0x110)==sprite+i*36
        else:
            assert word(u,b+0x110)==0xa5a5a5a5
        if i<loaded:
            raw=handles[77+i][0];indices=struct.unpack_from('<I',raw,20)[0];offset=44+indices*4
            assert bytes(u.mem_read(word(u,b),44))==raw[:44]
            assert bytes(u.mem_read(word(u,b+4),indices*4))==raw[44:offset]
            assert bytes(u.mem_read(word(u,b+8),len(raw)-offset))==raw[offset:]
        else:assert all(word(u,b+x)==0 for x in (0,4,8))
    prepares=[]
    if result:
        # Use actual loader outputs, retaining every configured bank index.
        put(u,0x6898d0,'I',directory);put(u,0x6894a0,'I',bank)
        rows=json.loads((ROOT/'modernization/docs/ai-action-registry.json').read_text())['actions']
        prior=json.loads((ROOT/'modernization/docs/ai-configured-prepare-verification.json').read_text())
        assert prior['result']=='passed' and prior['engine_sha256']==SHA
        config_raw=(RUNTIME/'CFG/effectani.cfg').read_bytes()
        assert prior['config_sha256']==hashlib.sha256(config_raw).hexdigest()
        timings={c['action_id']:c['steps'] for c in prior['cases']}
        for row in rows:
            action=row['action_id']
            if action not in OFFSETS:continue
            for delay in (0,7,40):
                a=0x2040000;put(u,MODE_FIELDS[action],'I',0)
                put(u,a+0x14e,'I',delay);put(u,a+0x162,'B',1)
                duration=call(u,int(row['methods']['prepare_execute'],16),a,[])
                assert duration==delay+(8 if action==39 else 5)+timings[action]
                assert bytes(u.mem_read(a+0x162,1))==b'\0'
                prepares.append(dict(action_id=action,delay=delay,steps=timings[action],duration=duration))
    return dict(result=result,entries=count,banks=files,loaded_banks=loaded,fail_sprite=fail_sprite,fail_ani=fail_ani,profile_calls=len(profile),allocations=len(allocations),sprite_binding_field='0x110',integrated_prepares=prepares)

def verify():
    path=RUNTIME/'CFG/effectani.cfg';raw=path.read_bytes();text=raw.decode('latin1');text=text[text.index('[HEADER]'):]
    assets={RUNTIME/'Sprites'/f'EFFECTS{i}.ANI':hashlib.sha256((RUNTIME/'Sprites'/f'EFFECTS{i}.ANI').read_bytes()).hexdigest() for i in range(13)}
    cfg=configparser.ConfigParser(inline_comment_prefixes=(';',),strict=False);cfg.read_string(text)
    cases=[fixture(cfg)]+[fixture(cfg,**{kind:i}) for kind in ('fail_sprite','fail_ani') for i in (0,6,12)]
    assert path.read_bytes()==raw
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in assets.items())
    report=dict(result='passed',engine_sha256=SHA,config_sha256=hashlib.sha256(raw).hexdigest(),asset_sha256={str(p):h for p,h in assets.items()},cases=cases,
        scope='Whole49c5b0, native59c441/49cc40/49cc70/464460 array constructors, all222 directory entries and native464b90 association plus whole4644d0 version5 loading for13 real ANI banks; resulting native directory/banks feed12 whole mode0 prepares for21/39/44/52, retaining actual bank indices. Win32 cwd/profile, CRT allocation/file IO and sprite57d310/57d690 explicit doubles; prepares have no additional doubles. Initial empty ownership only; sprite/ANI open failure at0/6/12 returns0 with allocated arrays retained. Bank+c remains0; sprite binding is+110. OS IO, sprite loading, reload/allocator/production failure cleanup and other actions/modes pending.')
    (ROOT/'modernization/docs/ai-effect-config-loader-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',cases=len(cases),entries=222,banks=13))

if __name__=='__main__':verify()
