"""Validate exception reproduction and paired owned save14 reload evidence."""
import json
import build_11_reload_surface as b
def main():
 root=b.b.ROOT/'modernization/logs/remastered-ui'
 before=root/'save14-reload-before-v4'
 events=[json.loads(x) for x in (before/'exception/events.jsonl').read_text().splitlines()]
 av=next(x for x in events if x.get('av')==1)
 assert av['eip']=='0x0058b40b' and av['fault']=='0x00000000' and av['esi']=='0x006c4e69'
 result=json.loads((before/'1.1/capture.json').read_text());assert result['reload_sequence']=='failed' and result['restored'] and not result['cleanup_errors']
 runs=[]
 for name in ['save14-reload-after-v1','save14-reload-after-active']:
  out=root/name;result=json.loads((out/'1.1/capture.json').read_text())
  assert result['reload_sequence']=='completed' and result['restored'] and not result['cleanup_errors'] and not result['timed_out']
  assert result['identity']['launcher_sha256']==b.b.sha(b.OUT/'candidate.exe')
  operations=[json.loads((out/f'operation-{i}.json').read_text()) for i in range(3)]
  assert all(o['before']!=o['after'] for o in operations)
  fixture=json.loads((out/'14-list.json').read_text())['fixture_sha256']
  assert fixture==json.loads((before/'14-list.json').read_text())['fixture_sha256']
  observation=dict(name=name,reloads=3,fixture_sha256=fixture,operations=operations)
  if (out/'exception/events.jsonl').exists():
   ev=[json.loads(x) for x in (out/'exception/events.jsonl').read_text().splitlines()]
   assert not any(x.get('exception')=='0xc0000005' for x in ev)
   observation['observer_detach']=ev[-1]
   # Detach returned0 on this owned run; cleanup still stopped only its child.
   # Use the following unobserved run as independent production-behavior gate.
  else:
   assert all(o['spell_target_mode']==2 for o in operations)
   observation['spell_scope']='Spell selection and cancellation; target did not accept the attempted cast, so spell execution is not certified.'
  runs.append(observation)
 v=json.loads((b.OUT/'verification.json').read_text());assert v['result']=='passed' and v['module_sha256']==b.b.sha(b.OUT/'qol_bindings.dll')
 v.update(save14_reload_verified=True,reproduction=av,owned_runs=runs,total_successful_reloads=6,runtime_acceptance='owned save14 six reloads passed,including three without debugger; installed user acceptance pending')
 b.base.write(b.OUT/'verification.json',v);print('Save14: six owned operation/reload cycles passed; root AV captured before fix')
if __name__=='__main__':main()
