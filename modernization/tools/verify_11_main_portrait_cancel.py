"""Compiled main portrait dispatch and native cast constructor; no gameplay."""
from pathlib import Path
import runpy
import build_11_main_portrait_cancel as build

# Reuse the verified native command fixture, switching only callback and target.
source=(build.b.ROOT/'modernization/tools/verify_11_teammate_portrait.py').read_text()
fixture=source.split('\nchecks=0\n')[0]
fixture=fixture.replace("remastered-1.1-teammate-portrait","remastered-1.1-main-portrait-cancel")
fixture=fixture.replace("sym('teammate_mouse_hook')","sym('portrait_cast_hook')")
fixture=fixture.replace("assert u.mem_read(0x463030,10)==bytes.fromhex('8a44240481ec00020000')",
 "assert u.mem_read(0x4d2b80,11)==bytes.fromhex('a12045640081ec00020000')")
fixture=fixture.replace('entry=0x463030','entry=0x4d2b80').replace("b'\\x90'*5","b'\\x90'*6")
fixture=fixture.replace('hook=sym(',"query=next(x.address for group in p.DIRECTORY_ENTRY_IMPORT for x in group.imports if x.name==b'VirtualQuery')\nhook=sym(",1)
fixture=fixture.replace('if a==readable:ret(0,1)',
 "if a==d(query):\n   ptr=d(sp+8);w(ptr,d(sp+4),d(sp+4),4,0x10000,0x1000,4,0x20000);ret(3,28)\n  elif a==readable:ret(0,1)")
fixture=fixture.replace('u.hook_add(UC_HOOK_CODE,trace)',
 'u.mem_map(d(query)&~4095,4096);u.hook_add(UC_HOOK_CODE,trace)')
fixture=fixture.replace("patched=True):","patched=True,cursor=16):").replace('w(0x5e04c8,16)','w(0x5e04c8,cursor)').replace('assert d(0x5e04c8)==16','assert d(0x5e04c8)==cursor')
fixture=fixture.replace("elif a==0x57cf40:",
 "elif a==0x4d2b8b:\n   events.append(('native-fallback',));u.reg_write(UC_X86_REG_ESP,sp+512);ret(11)\n  elif a==0x57cf40:")
ns={};exec(compile(fixture,__file__,'exec'),ns)
case=ns['case'];caster=ns['caster'];checks=0
for flags in [4,8,0x24,0x28,12,15]:
 events,payload,pending=case(flags)
 assert not payload and not any(e[0] in ('cast','native-fallback','select') for e in events)
 assert events==([('cancel',caster,0xffffffff)] if flags&8 else [])
 assert pending==(0xffffffff if flags&8 else 0)
 checks+=1
for flags in [2,0x22]:
 events,payload,pending=case(flags)
 assert events==[('cast',caster,16),('error-sound',)] and not payload and pending==0
 # Existing cursor predicate remains native: fixture cursor16 rejects casting.
 checks+=1
events,payload,pending=case(2,cursor=5)
assert events==[('cast',caster,5),('queue',0x6a2898)]
assert len(payload)==1 and (payload[0][0],payload[0][7],payload[0][8])==(41,77,77)
checks+=1
for kwargs in [dict(mode=0),dict(mode=1),dict(players=2),dict(pending=-1)]:
 for flags in [0,1,2,4,8,0x40]:
  assert case(flags,**kwargs)[0]==[('native-fallback',)]
  assert case(flags,**kwargs)==case(flags,patched=False,**kwargs)
  checks+=1
for flags in [0,1,0x40]:
 assert case(flags)[0]==[('native-fallback',)];checks+=1
# Full teammate suite must still pass against the same newly compiled module.
teammate=source.replace('remastered-1.1-teammate-portrait','remastered-1.1-main-portrait-cancel')
exec(compile(teammate,__file__,'exec'),{})
report=build.b.ROOT/'modernization/build/remastered-1.1-main-portrait-cancel/verification.json'
import json
other=json.loads(report.read_text())
build.base.write(report,dict(result='passed',checks=checks+other['checks'],main_checks=checks,
 teammate_checks=other['checks'],module_sha256=build.b.sha(build.OUT/'qol_bindings.dll'),
 scope='Compiled main hook ABI, right down consumed/right release native pending cancellation; left release native cast cursor validation unchanged; non-targeting and multiplayer fallback unchanged; 42 teammate regressions. Native readability/selection/queue/pending APIs stubbed; native cast constructor executed.',
 runtime_acceptance='pending user gameplay testing'))
print('Passed',checks+other['checks'],'main/teammate portrait checks')
