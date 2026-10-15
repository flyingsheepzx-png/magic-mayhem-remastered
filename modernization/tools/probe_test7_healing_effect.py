"""Observe native-surface and unit-state evidence for two portrait heal casts."""
import json
import os
import time
import sys,shutil

from wide169_trial import Session,ROOT,GAME,sha
from verify_hd60_runtime import read
from verify_wide169_input_map import state

os.environ['MM_ALLOW_NATIVE_CLIENT']='1'
os.environ['MM_ALLOW_SCALED_CLIENT']='1'

installed=GAME/'Chaos-Wide169-Trial.exe'
original=installed.read_bytes()
candidate_launcher=GAME/'Chaos-Wide169-Portrait-Diag.exe'
if '--candidate' in sys.argv:
    expected=json.loads((ROOT/'modernization/current-baseline.json').read_text())['latest_development']['files']['game/Chaos-Wide169-Trial.exe']
    if sha(original)!=expected:raise RuntimeError('Installed launcher identity mismatch')
    if candidate_launcher.exists():raise RuntimeError('Diagnostic launcher already exists')
    shutil.copy2(ROOT/'modernization/build/Chaos-Wide169-Trial.exe',candidate_launcher)
    os.environ['MM_WIDE169_DIAGNOSTIC_LAUNCHER']=str(candidate_launcher)
try:
 with Session() as s:
    s.load('test7')
    s.key(0x5a)
    wizard=s.i(0x6def58)
    def sample(label):
        raw=read(s.k,s.handle,wizard,0x120)
        return dict(label=label,t=time.monotonic(),state=state(s),
            words={hex(o):int.from_bytes(raw[o:o+4],'little',signed=True)
                   for o in range(0xa0,0xf0,4)})
    s.result['timeline']=[sample('before')]
    s.capture('before')
    s.key(ord('Q'));time.sleep(.2)
    s.result['timeline'].append(sample('armed'))
    s.capture('armed')
    target=(640,330) if '--world' in sys.argv else (1215,650)
    for click in (1,2):
        s.message(0x200,*target);time.sleep(.2)
        s.click(*target,right='--right' in sys.argv)
        s.result['timeline'].append(sample(f'click-{click}'))
        s.capture(f'click-{click}')
        for step in range(1,13):
            time.sleep(.25)
            s.result['timeline'].append(sample(f'click-{click}+{step/4:.2f}s'))
        s.capture(f'click-{click}-settled')
    print(json.dumps([dict(label=r['label'],mode=r['state']['mode'],icon=r['state']['icon'],
        hp_candidate=r['words']['0xe4'],mana_candidate=r['words']['0xec'])
        for r in s.result['timeline']],ensure_ascii=False))
finally:
 if '--candidate' in sys.argv:
    if sha(installed.read_bytes())!=sha(original):raise RuntimeError('Installed launcher changed')
    candidate_launcher.unlink()
