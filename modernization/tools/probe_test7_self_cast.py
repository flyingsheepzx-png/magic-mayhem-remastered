"""Reproduce Q healing on the wizard portrait in an owned widescreen session."""
import json
import os
import time
import sys

from wide169_trial import Session, ROOT, GAME, sha
from verify_wide169_input_map import state
from verify_hd60_runtime import read

os.environ['MM_ALLOW_NATIVE_CLIENT'] = '1'
os.environ['MM_ALLOW_SCALED_CLIENT'] = '1'

installed=GAME/'Chaos-Wide169-Trial.exe'
original=installed.read_bytes()
if '--candidate' in sys.argv:
    expected=json.loads((ROOT/'modernization/current-baseline.json').read_text())['latest_development']['files']['game/Chaos-Wide169-Trial.exe']
    if sha(original)!=expected:raise RuntimeError('Installed baseline mismatch')
    installed.write_bytes((ROOT/'modernization/build/Chaos-Wide169-Trial.exe').read_bytes())
try:
 with Session() as s:
    s.load('test7')
    s.key(0x5a)
    time.sleep(.2)
    s.result['before'] = state(s)
    s.key(ord('Q'))
    time.sleep(.2)
    s.result['armed'] = state(s)
    s.result['portrait_controls'] = [c for c in s.controls() if c['rect'][0] >= 1100 and c['rect'][1] >= 580]
    hero = s.i(0x6def58)
    snapshots=[read(s.k,s.handle,hero,0x800)]
    s.result['clicks']=[]
    for attempt in range(2):
        s.message(0x200,1215,650)
        time.sleep(.2)
        s.click(1215,650)
        time.sleep(.5)
        current=read(s.k,s.handle,hero,0x800)
        snapshots.append(current)
        s.result['clicks'].append(dict(attempt=attempt+1,state=state(s),
            resource_before=int.from_bytes(snapshots[-2][0xb0:0xb4],'little',signed=True),
            resource_after=int.from_bytes(current[0xb0:0xb4],'little',signed=True),
            changed_offsets=[hex(i) for i in range(0,0x7fc,4) if snapshots[-2][i:i+4]!=current[i:i+4]]))
        s.capture('after-self-cast-'+str(attempt+1))
    s.result['self_cast_verified']=(s.result['armed']['mode']==2 and
        all(row['state']['mode']==2 and row['state']['icon']==0 and
            row['state']['selected_count']==1 and row['state']['selected'][0]['pending']==0 and
            row['resource_after']<row['resource_before'] for row in s.result['clicks']))
    if not s.result['self_cast_verified']:
        raise RuntimeError('Two portrait casts did not both execute while spell remained armed')
    print(json.dumps({k:s.result[k] for k in ('armed','clicks','self_cast_verified')},ensure_ascii=False))
finally:
 if '--candidate' in sys.argv:
    installed.write_bytes(original)
    if sha(installed.read_bytes())!=sha(original):raise RuntimeError('Launcher restore failed')
