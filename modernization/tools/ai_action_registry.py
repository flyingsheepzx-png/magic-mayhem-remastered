"""Recover all static native AI prototype constructors and vtables."""
import hashlib,json,struct
from pathlib import Path
import pefile,capstone
ROOT=Path(__file__).resolve().parents[2]
SHA='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'

def recover():
 raw=(ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Chaos-Wide169-engine.exe').read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
 p=pefile.PE(data=raw);d=p.get_memory_mapped_image();base=p.OPTIONAL_HEADER.ImageBase
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 prototypes=[]
 for j in range(100):
  obj=struct.unpack_from('<I',d,0x5d8474-base+j*4)[0]
  if not obj:break
  prototypes.append(obj)
 constructors={};instructions=list(md.disasm(d[0x1000:0x7500],base+0x1000))
 for a,b in zip(instructions,instructions[1:]):
  if a.mnemonic=='mov' and len(a.operands)==2 and a.operands[0].type==capstone.CS_OP_REG and a.reg_name(a.operands[0].reg)=='ecx' and a.operands[1].type==capstone.CS_OP_IMM and a.operands[1].imm in prototypes and b.mnemonic=='call' and b.operands[0].type==capstone.CS_OP_IMM:
   constructors[a.operands[1].imm]=(a.address,b.operands[0].imm)
 assert len(constructors)==len(prototypes),(len(constructors),len(prototypes),[hex(x) for x in prototypes if x not in constructors])
 rows=[]
 for obj in prototypes:
  startup,ctor=constructors[obj];pushes=[];vtable=None;action=None
  for i in md.disasm(d[ctor-base:ctor-base+0x2000],ctor):
   if i.mnemonic=='ret':break
   if i.mnemonic=='push':pushes.append(i)
   if i.mnemonic=='call':
    if i.operands[0].type==capstone.CS_OP_IMM and i.operands[0].imm==0x417f20:
     assert pushes[-1].operands[0].type==capstone.CS_OP_IMM
     action=pushes[-1].operands[0].imm
    pushes=[]
   if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==capstone.CS_OP_MEM and i.operands[0].mem.disp==0 and i.operands[1].type==capstone.CS_OP_IMM and 0x5c5300<=i.operands[1].imm<0x5c5f00:vtable=i.operands[1].imm
   if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==capstone.CS_OP_MEM and i.operands[0].mem.disp==4 and i.reg_name(i.operands[0].mem.base)=='esi' and i.operands[1].type==capstone.CS_OP_IMM and 0<=i.operands[1].imm<100:action=i.operands[1].imm
  assert vtable is not None and action is not None,(hex(obj),hex(ctor),vtable,action)
  methods=struct.unpack_from('<7I',d,vtable-base)
  rows.append(dict(action_id=action,prototype=hex(obj),startup=hex(startup),constructor=hex(ctor),vtable=hex(vtable),methods={n:hex(a) for n,a in zip(['initialize','clone','evaluate','commit_or_copy','prepare_execute','execute','retire'],methods)}))
 return dict(engine_sha256=SHA,registry_va='0x5d8474',prototype_count=len(rows),actions=rows,
  note='Names are inferred interface roles from native indirect call sites, not recovered original C++ names')

if __name__=='__main__':
 d=recover();(ROOT/'modernization/docs/ai-action-registry.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
 print([(r['action_id'],r['constructor'],r['vtable']) for r in d['actions']])
