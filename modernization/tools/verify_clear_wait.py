"""Offline execution of v33 compiled wait hooks; no game process required."""
import json
import struct
import pefile
from unicorn.x86_const import *
from emulate_terrain_diagonal import Native
from install_clear_wait import installer as i

p = pefile.PE(str(i.BUILD/'repath.dll'))
base = p.OPTIONAL_HEADER.ImageBase
lines = (i.BUILD/'repath.map').read_text().splitlines()
def sym(name):
    return int(next(x for x in lines if '?'+name+'@@' in x).split()[2], 16)
unit = 0x1801000
regs = (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
        UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP)
def setup():
    n = Native(); u = n.u
    u.mem_map(base, (p.OPTIONAL_HEADER.SizeOfImage+4095)&~4095)
    u.mem_write(base, p.get_memory_mapped_image())
    n.w(0x6def58, unit); n.w(0x6def5c, 1); n.w(0x6e1f0c, 1)
    for off, value in [(0,1),(4,1),(0xe4,1),(0xac,0x1803000),
                       (0x5ec,2),(0x5fc,15),(0x97b,1)]: n.w(unit+off,value)
    n.w(0x1803008,1); n.w(0x180300c,4); n.w(0x1803044,1)
    for off, xyz in [(8,(54,74,5)),(0x97f,(54,73,6)),(0x96b,(53,73,5))]:
        u.mem_write(unit+off,struct.pack('<3i',*xyz))
    return n
def timer(n): return struct.unpack('<i',n.u.mem_read(unit+0x66c,4))[0]
def hook(n, name, end):
    u=n.u
    for k,r in enumerate(regs): u.reg_write(r,unit if r==UC_X86_REG_ESI else 0x123400+k)
    u.reg_write(UC_X86_REG_ESP,0x20ff000); u.reg_write(UC_X86_REG_EFLAGS,0x246)
    u.emu_start(sym(name),end,count=100000)
    assert u.reg_read(UC_X86_REG_ESP)==0x20ff000
    assert u.reg_read(UC_X86_REG_EFLAGS)==0x246
    for k,r in enumerate(regs):
        expected=unit if r==UC_X86_REG_ESI else 0x123400+k
        if name=='wait_tick_hook' and r==UC_X86_REG_EAX: expected=timer(n)
        assert u.reg_read(r)==expected
def arm(n): hook(n,'blocked_wait_hook',0x511be7)
def tick(n): hook(n,'wait_tick_hook',0x50f829)
def predicate(n, result):
    # Isolate state machine from external native terrain/occupancy predicates.
    n.u.mem_write(sym('walking_edge'),b'\xb0'+bytes([result])+b'\xc3')
    n.u.ctl_remove_cache(sym('walking_edge'),sym('walking_edge')+3)

checks=0
n=setup(); arm(n); predicate(n,0); tick(n); assert timer(n)==7
n.w(unit+0x66c,6); predicate(n,1); tick(n); assert timer(n)==1
checks+=2
n=setup(); n.w(unit+0x66c,7); predicate(n,1); tick(n); assert timer(n)==7
checks+=1
for address,value,size in [(0x6e1f0c,2,4),(unit+4,0,4),(unit+0xe4,0,4),
    (unit+0x5ec,14,4),(unit+0x5fc,2,4),(unit+0x618,1,4),
    (unit+0x104,1,4),(unit+0x10c,1,4),(unit+0x71c,1,1),(unit+0x723,1,1),
    (0x1803008,2,4),(0x1803044,2,4),(unit+0xac,0,4),
    (unit,2,4),(unit+8,53,4),(unit+0x97f,53,4),(unit+0x96b,52,4),
    (unit+0x977,1,4),(unit+0x97b,17,4),(unit+0x66c,8,4),(unit+0x66c,1,4)]:
    n=setup(); arm(n); predicate(n,1)
    n.u.mem_write(address,value.to_bytes(size,'little')); before=timer(n)
    tick(n); assert timer(n)==before
    checks+=1
for hook_name,end,delta in [('reset_hook',0x5060a7,8),('deserialize_hook',0x527316,0x148)]:
    n=setup(); arm(n); predicate(n,1)
    n.u.reg_write(UC_X86_REG_ECX,unit); n.u.reg_write(UC_X86_REG_ESP,0x20ff000)
    n.u.emu_start(sym(hook_name),end,count=100000)
    assert n.u.reg_read(UC_X86_REG_ESP)==0x20ff000-delta
    tick(n); assert timer(n)==7; checks+=1
# Exercise actual native space/headroom, occupancy and transition functions too.
n=setup(); arm(n); tick(n); assert timer(n)==1; checks+=1
n=setup(); arm(n)
cell=0x1000000+12*(54+80*73+6400*6)
n.u.mem_write(cell+10,struct.pack('<H',0x4000))
tick(n); assert timer(n)==7; checks+=1
report=dict(result='passed',checks=checks,dll_sha256=i.sha(i.BUILD/'repath.dll'),
    evidence='Compiled hook ABI/state/scope/lifecycle cases with predicate stub; real native validators on captured test10 map accept clear edge and reject solid destination',
    gameplay_tested=False)
i.write(i.BUILD/'wait-verification.json',report)
print(json.dumps(report))
