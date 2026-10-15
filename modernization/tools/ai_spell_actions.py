"""Associate native action initializers with fixed spell availability probes."""
import json,re,hashlib
from pathlib import Path
import pefile,capstone
ROOT=Path(__file__).resolve().parents[2]
EXPORTS=Path('D:/Tools/magic-mayhem-re/projects/ai-review-20261001/functions-registry')
def recover():
 registry=json.loads((ROOT/'modernization/docs/ai-action-registry.json').read_text())
 raw=(ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Chaos-Wide169-engine.exe').read_bytes();assert hashlib.sha256(raw).hexdigest()==registry['engine_sha256']
 pe=pefile.PE(data=raw);image=pe.get_memory_mapped_image();base=pe.OPTIONAL_HEADER.ImageBase
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
 config=Path('D:/Games/Magic&Mayham_Remastered_1.1/runtime/CFG/spells.cfg').read_text(encoding='latin1');spells={}
 for key,text in re.findall(r'\[SPELL_(\d+)\]([^\[]*)',config):
  fields=dict((k.strip(),v.split(';')[0].strip()) for k,v in re.findall(r'^([^=\n]+)=(.*)$',text,re.M))
  spells[int(key)]=fields
 rows=[]
 for action in registry['actions']:
  entry=int(action['methods']['initialize'],16);pushes=[];probes=[]
  for i in md.disasm(image[entry-base:entry-base+0x3000],entry):
   if i.mnemonic=='ret':break
   if i.mnemonic=='push':pushes.append(i)
   if i.mnemonic=='call':
    if i.operands[0].type==capstone.CS_OP_IMM and i.operands[0].imm==0x40a950:
     immediates=[x.operands[0].imm for x in reversed(pushes) if x.operands[0].type==capstone.CS_OP_IMM]
     assert immediates,(action,i)
     spell=immediates[0];assert spell in spells,(action['action_id'],spell)
     probes.append(dict(call_va=hex(i.address),spell_id=spell,spell_name=spells[spell].get('TextName'),config=spells[spell]))
    pushes=[]
  row=dict(action_id=action['action_id'],initialize=action['methods']['initialize'],spell_probes=probes)
  row['classification']='fixed-spell candidate' if probes else 'statistical tactical candidate' if 6<=action['action_id']<=14 else 'dynamic summoning candidate' if action['action_id']==15 else 'other heuristic candidate, semantics pending'
  rows.append(row)
 return dict(engine_sha256=registry['engine_sha256'],actions=rows,note='Availability probe proves associated fixed spell, not every targeting/scoring rule or successful cast')
if __name__=='__main__':
 d=recover();(ROOT/'modernization/docs/ai-spell-actions.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
 print([(r['action_id'],[(p['spell_id'],p['spell_name']) for p in r['spell_probes']]) for r in d['actions']])
