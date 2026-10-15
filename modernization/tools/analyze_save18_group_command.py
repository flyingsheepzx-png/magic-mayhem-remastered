"""Summarize captured save18 group orders; no game launch or memory writes."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOG=ROOT/'modernization/logs/remastered-ui'

def analyze(name,state,target=None,after=0):
 p=LOG/('save18-command-'+name)
 samples=json.loads((p/'samples.json').read_text())
 selected=[u['index'] for u in json.loads((p/'selected.json').read_text())['units'] if u['selected']]
 assert len(selected)==7
 def accepted(u):
  return u['target']==target if target is not None else u['pending']==state or u['state']==state
 issued=next(r for r in samples if r['seconds']>after and all(any(u['index']==i and accepted(u) for u in r['units']) for i in selected))
 rows=[]
 for i in selected:
  active=next(r for r in samples if r['seconds']>=issued['seconds'] and any(u['index']==i and u['state']==state for u in r['units']))
  rows.append(dict(unit=i,first_observed_request_tick=issued['game_time'],active_tick=active['game_time'],delay_ms=round(1000*(active['seconds']-issued['seconds']),1)))
 assert len({r['active_tick'] for r in rows})<len(rows),'Expected evidence of multiple units switching in a tick'
 report=dict(selected=selected,request_observed_seconds=issued['seconds'],request_observed_tick=issued['game_time'],transitions=rows,max_delay_ms=max(r['delay_ms'] for r in rows),
  caveat='Read-only polling snapshots, not per-instruction atomic traces. Timing measured in isolated diagnostic run; engine counter is not presentation FPS.')
 (p/'group-summary.json').write_text(json.dumps(report,indent=2)+'\n')
 return report

if __name__=='__main__':
 print(json.dumps(dict(attack=analyze('attack',3,8),move=analyze('move-followup',2,after=5.37)),indent=2))
