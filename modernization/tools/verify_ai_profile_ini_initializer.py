"""Whole465c60 against synthetic and shipped INI; native CRT token/number logic."""
import configparser,hashlib,json,re,struct,itertools
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX,UC_X86_REG_ECX
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT,SHA
from verify_ai_profile_selection import BASE,SIZE,word

RUNTIME=ROOT/'modernization/playtests/remastered-1.1-p1/runtime'
def cstr(u,p):
    raw=bytearray()
    while True:
        b=bytes(u.mem_read(p+len(raw),1))
        if b==b'\0':return raw.decode('latin1')
        raw.extend(b);assert len(raw)<1024

def oracle(entries,fill):
    expected=bytearray([fill]*SIZE);warnings=[];counts=[]
    for i in range(8):
        p=i*0x154
        for off in (0,4,8):word(expected,p+off,0)
        for off in (12,16,20):word(expected,p+off,-1)
        expected[p+0x18:p+0x20]=b'\x01'*8;expected[p+0x20:p+0x50]=bytes(48)
    word(expected,0xaa0,-1);word(expected,0xaa4,0)
    for i in range(8):
        raw=entries.get(f'Army_{i}','')[:255]
        if not raw:break
        p=i*0x154;word(expected,p,1);word(expected,p+8,1)
        tokens=[t.split('=')[0] for t in re.split('[, ]+',raw) if t]
        if not tokens:return expected,False,warnings+[0x5d97c8]
        name=tokens[0].encode('latin1')+b'\0';expected[p+0x50:p+0x50+len(name)]=name
        color=0;start=1
        if len(tokens)>1 and tokens[1] and tokens[1][0] in '0123456789':
            number=int(re.match(r'[0-9]+',tokens[1])[0]);number=((number+2**31)%2**32)-2**31
            if 0<=number<=7:color=number;start=2
            else:warnings.append(0x5d9860)
        else:warnings.append(0x5d9860)
        word(expected,p+0x150,color);relations=tokens[start:start+8]
        for j,rel in enumerate(relations):
            rel=rel.lower()
            if rel not in ('f','e','x'):return expected,False,warnings+[0x5d9800]
            if i!=j and rel!='x':
                expected[p+0x18+j]=int(rel=='f');expected[j*0x154+0x18+i]=int(rel=='f')
        counts.append(len(relations))
    if not counts:return expected,False,warnings+[0x5d9784]
    if any(n!=len(counts) for n in counts):return expected,False,warnings+[0x5d970c]
    return expected,True,warnings

def fixture(entries,region=0,fill=165,cwd='X:\\isolated',path='Realms\\Fixture\\Fixture.cfg'):
    u=machine();u.mem_write(BASE,bytes([fill])*SIZE);put(u,0x656620,'I',region)
    u.mem_write(0x6ddd58,path.encode()+b'\0')
    cwd_api=0x2030000;profile_api=cwd_api+16
    put(u,0x5c50bc,'I',cwd_api);put(u,0x5c507c,'I',profile_api)
    u.mem_write(cwd_api,b'\xc2\x08\x00');u.mem_write(profile_api,b'\xc2\x18\x00')
    u.mem_write(0x59c1fd,b'\xc3');u.mem_write(0x49e680,b'\xc3')
    queries=[];errors=[];formats=[]
    expected,valid,warnings=oracle(entries,fill)
    def boundary(uc,address,size,user):
        if address not in (cwd_api,profile_api,0x59c1fd,0x49e680):return
        sp=uc.reg_read(UC_X86_REG_ESP)
        if address==cwd_api:
            n,out=struct.unpack('<2I',uc.mem_read(sp+4,8));assert n==256
            uc.mem_write(out,cwd.encode()+b'\0');uc.reg_write(UC_X86_REG_EAX,len(cwd))
        elif address==profile_api:
            section,key,default,out,n,filename=struct.unpack('<6I',uc.mem_read(sp+4,24))
            sec=cstr(uc,section);key=cstr(uc,key)
            assert sec==f'REGION{region}' and n==256 and cstr(uc,default)==''
            assert cstr(uc,filename)==cwd+('' if not cwd or cwd[-1] in '/\\' else '\\')+path
            raw=entries.get(key,'').encode('latin1')[:n-1]
            uc.mem_write(out,raw+b'\0');uc.reg_write(UC_X86_REG_EAX,len(raw));queries.append(key)
        elif address==0x59c1fd:
            out,fmt,index=struct.unpack('<3I',uc.mem_read(sp+4,12));formatstr=cstr(uc,fmt)
            assert formatstr in ('REGION%d','Army_%i')
            raw=(formatstr.replace('%d',str(index)).replace('%i',str(index))).encode()
            uc.mem_write(out,raw+b'\0');uc.reg_write(UC_X86_REG_EAX,len(raw));formats.append(formatstr)
        else:
            errors.append(uc.reg_read(UC_X86_REG_ECX));uc.reg_write(UC_X86_REG_EAX,0x12345678)
    u.hook_add(UC_HOOK_CODE,boundary)
    result=call(u,0x465c60,BASE,[])&255
    assert result==valid,(entries,result,valid)
    assert errors==warnings,(entries,errors,warnings)
    actual=bytes(u.mem_read(BASE,SIZE))
    assert actual==expected,[(hex(i),actual[i],expected[i]) for i in range(SIZE) if actual[i]!=expected[i]][:12]
    assert u.reg_read(UC_X86_REG_ESP)==0x23f0004
    assert struct.unpack('<I',u.mem_read(0x5fbf28,4))[0]==BASE
    return dict(region=region,fill=fill,cwd=cwd,entries=entries,result=result,queries=queries,error_messages=[hex(e) for e in errors])

def verify():
    synthetic=[]
    for count,pattern,fill,cwd in itertools.product(range(1,9),range(3),(0,165,255),('X:\\isolated','X:\\isolated\\','X:/isolated/')):
        entries={f'Army_{i}':f'Name{i},{i},'+','.join(('F','e','X')[(i+j+pattern)%3] for j in range(count)) for i in range(count)}
        synthetic.append(fixture(entries,fill=fill,cwd=cwd))
    malformed=[{}, {'Army_0':' , , '},{'Army_0':'Name,0,?'},{'Army_0':'Name,0'},
        {'Army_0':'Name,F'},{'Army_0':'Name,9,F'},{'Army_0':'Name,7suffix,F'},
        {'Army_0':'Name=ignored,3,F'},{'Army_0':'Name,0,F','Army_2':'Skipped,1,F'},
        {'Army_0':'A,0,F,F','Army_1':'B,1,E'}, {'Army_0':'Name,-1,F'},
        {'Army_0':'Name,4294967296,F'}]
    synthetic.extend(fixture(e,fill=f) for e,f in itertools.product(malformed,(0,165,255)))
    production=[];sources=[]
    for realm in ('Celtic','Greek','Medieval'):
        path=RUNTIME/'Realms'/realm/f'{realm}.cfg';raw=path.read_bytes()
        cfg=configparser.ConfigParser(interpolation=None,strict=False,inline_comment_prefixes=(';',));cfg.optionxform=str.lower
        cfg.read_string(raw.decode('latin1'))
        sources.append(dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest()))
        for sec in cfg.sections():
            if not re.fullmatch('REGION[0-9]+',sec):continue
            entries={f'Army_{i}':cfg[sec][f'army_{i}'] for i in range(8) if f'army_{i}' in cfg[sec]}
            production.append(dict(realm=realm,section=sec,case=fixture(entries,int(sec[6:]),path=f'Realms\\{realm}\\{realm}.cfg')))
        assert hashlib.sha256(path.read_bytes()).hexdigest()==sources[-1]['sha256']
    report=dict(result='passed',engine_sha256=SHA,synthetic_cases=synthetic,production_cases=production,sources=sources,
        scope='Whole465c60. OnlyWin32 cwd/profile,CRT sprintf,anderror display doubled. Actualstrtok59c99c,strchr59c8e0,isdigit59c6e7,atoi59c5a4/59c519,stricmp59db40 execute with diskC-locale tables. Fullaa8 snapshots/AL/stack/globalpointer/errors independentlychecked. Synthetic8slot/mixedrelation/cwd/failure domains andallREGION sections ofthree shipped realmconfigs. No gameIO/playerchanges. API/localization/INI semantics outside fixtures,subsequentrole/wizard/20-28tablewriters/save/network pending.')
    (ROOT/'modernization/docs/ai-profile-ini-initializer-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(dict(result='passed',synthetic=len(synthetic),production=len(production),production_failed=sum(not p['case']['result'] for p in production)))

if __name__=='__main__':verify()
