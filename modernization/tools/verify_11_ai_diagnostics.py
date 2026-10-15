"""Offline compiled x86-hook and observer checks; never launches the game."""
import json
import struct
import subprocess
from pathlib import Path
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
import build_remastered_11 as b

HOOKS=[
 ('begin',0x415c40,6,[0x415c46]),('end',0x41651b,5,[0x416520]),
 ('model_begin',0x4766b0,7,[0x4766b7]),('model_end',0x476b26,10,[0x476b30]),
 ('eval1',0x428674,8,[0x42867c,0x4288df]),('eval2',0x4288d4,8,[0x42867c,0x4288dc]),
 ('eligible',0x428751,5,[0x428756]),('again',0x4288be,6,[0x4288c4]),
 ('yield',0x428936,9,[0x42893f]),('commit',0x4289e0,5,[0x4289e5]),
 ('execute',0x4164de,5,[0x4164e3]),('retire',0x428c4c,8,[0x428c54,0x428e18])]
GPRS=[UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_EBX,
      UC_X86_REG_ESP,UC_X86_REG_EBP,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EFLAGS]
STOP=0x20fe000;STACK=0x20ff000

class Machine:
    def __init__(self,dll,stub_observer=False,write_ok=True):
        engine=b.TARGET/'runtime/Chaos-Wide169-engine.exe'
        assert b.sha(engine)=='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
        self.u=Uc(UC_ARCH_X86,UC_MODE_32)
        self.u.mem_map(0,0x10000);self.w(0,0xffffffff) # offline SEH chain / FS:[0]
        ep=pefile.PE(str(engine));self.u.mem_map(0x400000,0x400000)
        self.u.mem_write(0x400000,ep.get_memory_mapped_image());ep.close()
        dp=pefile.PE(str(dll));self.base=dp.OPTIONAL_HEADER.ImageBase
        self.u.mem_map(self.base,(dp.OPTIONAL_HEADER.SizeOfImage+4095)&~4095)
        self.u.mem_write(self.base,dp.get_memory_mapped_image())
        self.exports={s.name.decode().lstrip('_'):self.base+s.address for s in dp.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
        self.u.mem_map(0x2000000,0x100000);self.u.mem_map(0x3000000,0x100000)
        self.u.mem_map(0x3100000,0x10000);self.last_error=99;self.qpc=1000;self.writes=[];self.calls=[]
        apis={};slot=0x3100000
        for desc in dp.DIRECTORY_ENTRY_IMPORT:
            for imp in desc.imports:
                name=imp.name.decode() if imp.name else '#'+str(imp.ordinal)
                self.w(imp.address,slot);apis[slot]=name;slot+=16
        dp.close()
        observer=self.exports['mm_ai_observe']
        if stub_observer:
            # Cdecl callback deliberately dirties volatile integer/FP/SSE state.
            self.u.mem_write(observer,bytes.fromhex('dbe3d9e80fefc0b8deadbeefb934120000ba7856000083f001c3'))
        def code(u,address,size,user):
            if address in apis:
                name=apis[address];self.calls.append(name);sp=u.reg_read(UC_X86_REG_ESP)
                ret=self.d(sp);eax=0;argc=0
                if name=='GetLastError':eax=self.last_error
                elif name=='SetLastError':self.last_error=self.d(sp+4);argc=1
                elif name=='QueryPerformanceCounter':
                    argc=1;self.qpc+=100;u.mem_write(self.d(sp+4),struct.pack('<q',self.qpc));eax=1
                elif name=='WriteFile':
                    argc=5;buf,n=self.d(sp+8),self.d(sp+12)
                    if write_ok:self.w(self.d(sp+16),n);self.writes.append(bytes(u.mem_read(buf,n)));eax=1
                elif name=='CloseHandle':argc=1;eax=1
                else:raise AssertionError('Unexpected API '+name)
                u.reg_write(UC_X86_REG_EAX,eax);u.reg_write(UC_X86_REG_ESP,sp+4+4*argc);u.reg_write(UC_X86_REG_EIP,ret)
        self.u.hook_add(UC_HOOK_CODE,code)
    def w(self,a,v):self.u.mem_write(a,struct.pack('<I',v&0xffffffff))
    def d(self,a):return struct.unpack('<I',self.u.mem_read(a,4))[0]
    def call(self,name,args=()):
        self.u.mem_write(STACK,struct.pack('<'+'I'*(len(args)+1),STOP,*args))
        self.u.reg_write(UC_X86_REG_ESP,STACK)
        self.u.emu_start(self.exports[name],STOP,count=500000)
        assert self.u.reg_read(UC_X86_REG_EIP)==STOP,'unfinished emulation'
        return self.u.reg_read(UC_X86_REG_EAX)
    def setup(self,value=1):
        for reg,n in zip(GPRS,[0x12340000|value,0x3004000,0x24680000,0x3005000|value,STACK,0x20fd000,0x3000000,0x3002000,0x602]):self.u.reg_write(reg,n)
        for a in range(STACK-64,STACK+256,4):self.w(a,0x3006000)
        self.w(0x20fd000,0x3006000);self.w(0x20fd008,0x3f123456);self.w(0x20fcff8,0x3005000)
        self.w(0x3005000,0x3006000);self.w(0x3000014,43)
        # Full x87 stack, nondefault rounding mode and live XMM register values.
        self.u.mem_write(0x2001000,bytes.fromhex('dbe3')+bytes.fromhex('d9e8')*8+bytes.fromhex('d92d00120002'))
        self.u.mem_write(0x2001200,struct.pack('<H',0xb7f))
        self.u.emu_start(0x2001000,0x2001000+24)
        for i in range(8):self.u.reg_write(UC_X86_REG_XMM0+i,(i+1)*0x123456789abcdef)
    def fpstate(self):
        self.u.mem_write(0x2001400,bytes.fromhex('0fae0500150002'))
        self.u.emu_start(0x2001400,0x2001407)
        return bytes(self.u.mem_read(0x2001500,512))
    def run_to(self,start,stops):
        # Stop at continuation before any subsequent native instruction executes.
        def halt(u,address,size,data):
            if address in stops:u.emu_stop()
        h=self.u.hook_add(UC_HOOK_CODE,halt)
        self.u.emu_start(start,0,count=10000);self.u.hook_del(h)
        assert self.u.reg_read(UC_X86_REG_EIP) in stops

def verify(out):
    dll=out/'ai_diagnostics.dll';checks=[]
    for name,site,length,stops in HOOKS:
        for value in [0,1,255]:
            native=Machine(dll,True);hook=Machine(dll,True)
            native.setup(value);hook.setup(value)
            native.run_to(site,stops);hook.run_to(hook.exports['mm_ai_'+name+'_hook'],stops)
            assert [native.u.reg_read(r) for r in GPRS]==[hook.u.reg_read(r) for r in GPRS],(name,value,'registers')
            assert native.u.reg_read(UC_X86_REG_EIP)==hook.u.reg_read(UC_X86_REG_EIP),(name,value,'branch')
            fp_native,fp_hook=native.fpstate(),hook.fpstate()
            # Unicorn does not restore x87 last-instruction pointer on FXRSTOR.
            # Real x86 fixture below separately checks all 512 bytes INCLUDING IP.
            assert fp_native[:8]+fp_native[16:]==fp_hook[:8]+fp_hook[16:],(name,value,'floating point/SSE')
            assert native.u.mem_read(0x3000000,0x13000)==hook.u.mem_read(0x3000000,0x13000),(name,value,'game objects')
            # Original stack above final ESP must be byte-identical; temporary
            # PUSHAD/FXSAVE area below ESP is intentionally scratch space.
            finalsp=native.u.reg_read(UC_X86_REG_ESP)
            live=max(STACK,finalsp)
            assert native.u.mem_read(live,0x2100000-live)==hook.u.mem_read(live,0x2100000-live),(name,value,'stack')
            # Prologues reserve uninitialized local slots; their bytes need not
            # match callback scratch, but each actual saved register must match.
            for a,n in ({'begin':[(STACK-4,4)],'model_begin':[(STACK-8,8)],
                         'commit':[(STACK-24,8)]}.get(name,[])):
                assert native.u.mem_read(a,n)==hook.u.mem_read(a,n),(name,value,'saved stack registers')
            checks.append(name+':'+str(value))
    # Compile same observer source, exposing test state ONLY in fixture DLL.
    import shutil
    shutil.copy2(b.ROOT/'modernization/tests/ai_diagnostics_fp_test.cpp',out/'ai_diagnostics_fp_test.cpp')
    cmd='''@echo off
call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /LD /O2 /EHsc /std:c++17 /DMM_AI_TEST ai_diagnostics.cpp /link /OUT:ai_fixture.dll bcrypt.lib user32.lib
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 ai_diagnostics_fp_test.cpp /link /OUT:ai_diagnostics_fp_test.exe
if errorlevel 1 exit /b 1
ai_diagnostics_fp_test.exe
'''
    (out/'fixture.cmd').write_text(cmd);subprocess.run(['cmd','/c','fixture.cmd'],cwd=out,check=True)
    fixture=out/'ai_fixture.dll'
    checks.append('real x86 full CPU/FP/SSE/DF/LastError callback preservation off/on')
    m=Machine(fixture);m.call('mm_ai_test_begin')
    r=0x2005000;sp=0x20fc000;ctx=0x3000000;group=0x3002000;action=0x3006000;vec=0x3008000
    m.w(ctx,1);m.w(ctx+0x14,43);m.w(ctx+0x11dab,4);m.w(ctx+0x11fe5,0x3005000)
    m.w(0x3005000,action);m.w(action,0x5c596c);m.w(action+4,6);m.w(action+8,group);m.w(action+0x27,123)
    m.w(group+5,0x3007000);m.w(0x3007004,8)
    bp=0x20fd000;m.w(bp-8,0x3005000);m.w(bp+8,0x3f000000);m.w(bp+0xc,vec);m.w(vec+8,0)
    def observe(kind,regs=None):
        values=[group,ctx,bp,sp-4,0x3005000,0,ctx,1,0x602]
        if regs:
            for k,v in regs.items():values[k]=v
        m.u.mem_write(r,struct.pack('<9I',*values));m.call('mm_ai_observe',[kind,r]);assert m.last_error==99
    m.w(sp+4,15);observe(1)
    observe(5);observe(9);m.w(sp+4,group);observe(10);observe(11,{0:action,7:0})
    count=m.call('mm_ai_test_count');ptr=m.call('mm_ai_test_events');rows=[struct.unpack('<100I',m.u.mem_read(ptr+400*i,400)) for i in range(count)]
    assert rows[0][14-1]==15 and rows[1][8]==6 and rows[1][15]==0x3f000000
    assert rows[3][12]==8 and rows[3][8]==6 and rows[4][14]==0
    checks.append('observer candidate/id/score/budget/old-action/execution/last-error')
    # Native model input/output exact stack offsets, vector capture and counts.
    m.w(sp+4,6);m.w(sp+8,vec);m.w(vec+4,0x3009000);m.w(vec+8,0x300900c)
    for i,x in enumerate([1,9,0xffffffff]):m.w(0x3009000+4*i,x)
    observe(3)
    m.w(sp+0xe0,6);m.w(sp+0xe8,3);m.w(sp+0xec,0x300a000)
    for i,x in enumerate([0x3e800000,0x3f000000,0x3e800000]):m.w(0x300a000+4*i,x)
    observe(4);count=m.call('mm_ai_test_count');ptr=m.call('mm_ai_test_events')
    last=[struct.unpack('<100I',m.u.mem_read(ptr+400*i,400)) for i in range(count-2,count)]
    assert list(last[0][20:23])==[1,9,0xffffffff] and list(last[1][20:23])==[0x3e800000,0x3f000000,0x3e800000]
    checks.append('model vectors/probabilities and original native stack offsets')
    # Disabled, multiplayer and file-size/failure gates.
    m.w(0x6e1f0c,1);observe(10);assert m.call('mm_ai_test_count')==count;m.w(0x6e1f0c,0)
    observe(2);assert len(m.writes)==1 and m.call('mm_ai_test_count')==0
    m.call('mm_ai_test_cap');observe(10);observe(2);assert m.call('mm_ai_test_active')==0
    checks.append('multiplayer exclusion, scheduler-end batch flush, size cap')
    bad=Machine(fixture,write_ok=False);bad.call('mm_ai_test_begin');bad.u.mem_write(r,struct.pack('<9I',group,ctx,bp,sp-4,0,0,ctx,0,0));bad.call('mm_ai_observe',[2,r]);assert bad.call('mm_ai_test_active')==0
    checks.append('write failure disables logging')
    from read_ai_diagnostics_11 import decode,summarize,ENGINE
    testfile=out/'fixture-trace.bin';testfile.write_bytes(struct.pack('<8sII64s',b'MM_AI11\0',1,400,ENGINE.encode())+m.writes[0])
    decoded=list(decode(testfile));assert len(decoded)==count+1
    assert next(e for e in decoded if e['kind']==3)['features_i32']==[1,9,-1]
    assert next(e for e in decoded if e['kind']==4)['probabilities']==[.25,.5,.25]
    assert summarize(decoded)['committed_action_ids']=={6:1}
    checks.append('actual emitted binary decoder and summary')
    # Only the exact argument opts in, no inherited environment activation.
    for name in ['launcher.cpp','release_launcher.cpp']:
        text=(out/name).read_text(encoding='utf-8')
        assert 'value.substr(first,last-first+1)!=L"--ai-trace"' in text
        assert text.index('SetEnvironmentVariableW(L"MM_AI_TRACE",nullptr)')<text.index('CopyFileW(source.c_str(),dest.c_str(),TRUE)')
        assert text.index('prepare_ai_trace(game,arguments,ai_directory)')<text.index('CreateProcessW(exe.c_str()')
        assert 'if(!ai_directory.empty())' in text
    checks.append('default-off launcher gate and pre-launch snapshots')
    return {'checks':len(checks),'evidence':checks,'gameplay_tested':False}
