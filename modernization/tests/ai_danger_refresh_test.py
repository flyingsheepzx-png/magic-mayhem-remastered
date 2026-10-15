"""Production compiled hooks, native perception and publication fixtures; no game."""
import hashlib,itertools,json,struct,sys
from pathlib import Path
import pefile
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'modernization/tools'))
from verify_ai_training_math import machine,put
from verify_ai_model_native import SHA
OUT=ROOT/'modernization/build/remastered-1.1-danger-refresh'
pe=pefile.PE(str(OUT/'qol_bindings.dll'));base=pe.OPTIONAL_HEADER.ImageBase;image=pe.get_memory_mapped_image()
symbols={s.name.decode().lstrip('_'):base+s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
def patched(mode=0):
 u=machine();u.mem_map(base,(len(image)+4095)&~4095);u.mem_write(base,image);put(u,0x6e1f0c,'I',mode)
 for site,name,size in [(0x41dbfd,'mm_danger_units_hook',9),(0x41d3fc,'mm_danger_cells_hook',9),(0x41d486,'mm_danger_rotation_hook',8)]:
  u.mem_write(site,b'\xe9'+struct.pack('<i',symbols[name]-site-5)+b'\x90'*(size-5))
 return u
checks=0
for mode,value in itertools.product((0,1,2),(-1,0,3,4,15,16,17,31,32,127,128,129)):
 for units in (True,False):
  u=patched(mode);m=0x2010000;put(u,m+0x1209d,'I',99)
  regs={UC_X86_REG_EAX:value&0xffffffff,UC_X86_REG_EBX:0x123456,UC_X86_REG_ECX:0x789abc,
        UC_X86_REG_EDX:0xfedcba,UC_X86_REG_ESI:m if units else value&0xffffffff,
        UC_X86_REG_EDI:7,UC_X86_REG_EBP:0x2020000,UC_X86_REG_ESP:0x23f0000}
  for r,v in regs.items():u.reg_write(r,v)
  stop=0x41dc06 if units else (0x41dc10 if value==(128 if mode==0 else 32) else 0x41d405)
  u.emu_start(symbols['mm_danger_units_hook' if units else 'mm_danger_cells_hook'],stop,count=100)
  flags=u.reg_read(UC_X86_REG_EFLAGS)&0x8d5
  assert u.reg_read(UC_X86_REG_EIP)==stop
  for r,v in regs.items():assert u.reg_read(r)==v
  if units:assert struct.unpack('<I',u.mem_read(m+0x1209d,4))[0]==7
  # Compare hook flags with actual CMP on the same input and chosen limit.
  limit=(16 if mode==0 else 4) if units else (128 if mode==0 else 32)
  scratch=0x2000000
  u.mem_write(scratch,(b'\x3d' if units else b'\x81\xfe')+struct.pack('<I',limit))
  u.emu_start(scratch,scratch+(5 if units else 6),count=5)
  assert u.reg_read(UC_X86_REG_EFLAGS)&0x8d5==flags
  checks+=1

rotation_checks=0
for mode,spent,marker in itertools.product((0,1,2),(0,7,8),(0,1)):
 u=patched(mode);m=0x2010000;put(u,m+0x12098,'B',marker)
 regs={UC_X86_REG_EAX:8,UC_X86_REG_ECX:spent,UC_X86_REG_EDI:m,UC_X86_REG_ESP:0x23f0000}
 for r,v in regs.items():u.reg_write(r,v)
 stop=0x41dc10 if spent==8 else 0x41d48e
 u.emu_start(symbols['mm_danger_rotation_hook'],stop,count=100)
 assert u.reg_read(UC_X86_REG_EIP)==stop
 for r,v in regs.items():assert u.reg_read(r)==v
 assert bytes(u.mem_read(m+0x12098,1))[0]==(1 if mode==0 and spent==8 else marker)
 rotation_checks+=1

# Reuse independent native reference assertions without changing historical tests.
def load(name,replacements):
 p=ROOT/'modernization/tools'/name;s=p.read_text(encoding='utf-8').split('\ndef verify():')[0]
 for a,b in replacements:s=s.replace(a,b)
 ns={'__name__':'fixture'};exec(compile(s,str(p),'exec'),ns);ns['machine']=patched
 def bounded_call(u,entry,this,args):
  sp=0x23f0000;stop=0x2000000;put(u,sp,'I'*(1+len(args)),stop,*args)
  u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,this)
  u.emu_start(entry,stop,count=2000000);assert u.reg_read(UC_X86_REG_EIP)==stop
  return u.reg_read(UC_X86_REG_EAX)
 ns['call']=bounded_call;return ns
pub=load('verify_ai_danger_publication.py',[('n=min(32,','n=min(128,')])
publication=[pub['fixture'](owner,count,start,False) for owner,count in itertools.product((0,7),(0,1,127,128,129,256,257)) for start in sorted({0,count//2,count})]
publication.extend(pub['fixture'](owner,count,0,True) for owner,count in itertools.product(range(8),(1,33,65)))
pipe=load('verify_ai_danger_pipeline.py',[("assert round_events.count('unit')<=4","assert round_events.count('unit')<=16"),
 ("elif address==0x41d476 and word(uc,m+0x12099)==owner:","elif address==0x41d476 and word(uc,m+0x12099)==owner and pending[0]>0:"),
 ("assert pending[0]==active and next_unit[0]==active","assert pending[0]==active and next_unit[0]==active,(active,count,kind,status,spatial,effects,owner,pending[0],next_unit[0])")])
pipeline=[pipe['fixture'](active,count,kind,status,spatial,effects,owner) for active,count,kind,status,spatial,effects,owner in
 [(a,c,k,st,sp,ef,o) for a,c,k,st,sp,ef,o in itertools.product((5,9,17),(4,65),(0,1),(0,1),(None,'reverse'),(False,True),(0,7)) if not(st and k==1)]]
multi=load('verify_ai_danger_multiowner.py',[('assert round_units[0]<=4','assert round_units[0]<=16'),
 ('assert position[owner]==len(sequences[owner])','assert position[owner]==len(sequences[owner]),("position",count,relations,filters,owner,position,sequences)'),
 ('assert word(uc,wizard+0x926)==sum(values[owner])==pending[owner]','assert word(uc,wizard+0x926)==sum(values[owner])==pending[owner],("total",count,relations,filters,owner,word(uc,wizard+0x926),values[owner],pending)'),
 ('assert list(uc.mem_read(cells+i*0x294+0x24c+slot*7,7))==expected','assert list(uc.mem_read(cells+i*0x294+0x24c+slot*7,7))==expected,("map",count,relations,filters,owner,slot,i,list(uc.mem_read(cells+i*0x294+0x24c+slot*7,7)),expected)'),
 ('def hook(uc,address,size,user):','publication_marker=[False]\n    def hook(uc,address,size,user):\n        if address==0x542be0:publication_marker[0]=True'),
 ('elif address==0x41d476 and word(uc,m+0x12099) in owners:',
  'elif address==0x41d476 and word(uc,m+0x12099) in owners and publication_marker[0]:\n            publication_marker[0]=False')])
multi_cases=[multi['fixture'](*v) for v in itertools.product((4,33),range(4),range(4))]
report=dict(result='passed',engine_sha256=SHA,module_sha256=hashlib.sha256((OUT/'qol_bindings.dll').read_bytes()).hexdigest(),
 compiled_hook_checks=checks,rotation_hook_checks=rotation_checks,publication_fixtures=len(publication),whole_pipeline_fixtures=len(pipeline),multiowner_fixtures=len(multi_cases),
 singleplayer_limits=dict(processed_units=16,finalized_cells=128),multiplayer_limits=dict(processed_units=4,finalized_cells=32),
 retained_ai_budget=300,unchanged_modules=[101,103],runtime_acceptance='pending user testing; no game launched',
 scope='Compiled comparisons/registers/flags/stack; whole native producer with only CRT alloc/free doubled, actual effects/graphs/owners and continuation across17units; publication boundaries through257cells with explicit finalizer double plus actual effects through65cells; all asymmetric two-owner relations.')
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
