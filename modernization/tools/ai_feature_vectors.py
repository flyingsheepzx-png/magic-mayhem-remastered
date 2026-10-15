"""Recover literal feature selector order at each action's native varargs call."""
import hashlib,json,struct
from pathlib import Path
import pefile,capstone
ROOT=Path(__file__).resolve().parents[2]
SHA='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
ENTRIES=[(6,0x431ce0,0x4328d0),(7,0x4330c0,0x433ca0),(8,0x434500,0x435a90),(9,0x4369d0,0x437650),(10,0x4379d0,0x4389d0),(11,0x438c70,0x439b40),(12,0x43a000,0x43b260),(13,0x43b4c0,0x43c390),(14,0x43c800,0x43d410)]

def recover():
 raw=(ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Chaos-Wide169-engine.exe').read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
 p=pefile.PE(data=raw);d=p.get_memory_mapped_image();base=p.OPTIONAL_HEADER.ImageBase
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 dictionary=json.loads((ROOT/'modernization/docs/ai-config-dictionary.json').read_text())
 names={r['parameter_slot']+1:r['key'] for r in dictionary['rows']}
 actions=[]
 for action,start,end in ENTRIES:
  pushes=[];calls=[]
  for ins in md.disasm(d[start-base:end-base],start):
   if ins.mnemonic=='push':pushes.append(ins)
   if ins.mnemonic=='call':
    if ins.operands[0].type==capstone.CS_OP_IMM and ins.operands[0].imm==0x40b420:
     rev=list(reversed(pushes));assert len(rev)>5
     count=rev[4].operands[0].imm;assert count>0 and len(rev)>=count+5
     selected=rev[5:5+count];assert all(x.operands[0].type==capstone.CS_OP_IMM for x in selected)
     ids=[x.operands[0].imm for x in selected]
     calls.append(dict(call_va=hex(ins.address),base_dimension=count,selectors=[dict(index=i,selector=x,key=names.get(abs(x))) for i,x in enumerate(ids)]))
    pushes=[]
  assert len(calls)==1,(action,calls)
  table=0x5c596c+(action-6)*28;methods=struct.unpack_from('<7I',d,table-base)
  actions.append(dict(action_id=action,vtable=hex(table),methods={name:hex(address) for name,address in zip(['initialize','clone','evaluate','commit_or_copy','prepare_execute','execute','retire'],methods)},feature_calls=calls))
 return dict(engine_sha256=SHA,feature_builder='0x40b420',threshold_binding_base='0x5f8260',actions=actions,
 note='selector names recover from native abs(selector)*4 parameter addressing at0x40ea00; model vectors also append action-specific values not included in base_dimension')

if __name__=='__main__':
 result=recover();(ROOT/'modernization/docs/ai-feature-vectors.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print([(a['action_id'],a['feature_calls'][0]['base_dimension']) for a in result['actions']])
