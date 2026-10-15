"""Exercise all three reported regressions against the staged candidate."""
import json
import time
import os
from pathlib import Path
from PIL import Image

from wide169_trial import ROOT, LAB, GAME, Session, sha
from verify_wide169_input_map import state

build=ROOT/'modernization/build'
assets=build/'wide169/followup-assets'
candidate={
    GAME/'Chaos-Wide169-Trial.exe':build/'Chaos-Wide169-Trial.exe',
    LAB/'Chaos-Wide169-engine.exe':build/'wide169/Chaos-Wide169-engine.exe',
}
for source in assets.rglob('*'):
    if source.is_file():candidate[LAB/source.relative_to(assets)]=source
if not all(p.is_file() and q.is_file() for p,q in candidate.items()):
    raise RuntimeError('Incomplete candidate')
original={p:p.read_bytes() for p in candidate}
os.environ['MM_ALLOW_NATIVE_CLIENT']='1'
os.environ['MM_ALLOW_SCALED_CLIENT']='1'
report={'original_hashes':{str(p):sha(data) for p,data in original.items()},
        'candidate_hashes':{str(p):sha(q.read_bytes()) for p,q in candidate.items()}}
try:
    for p,source in candidate.items():p.write_bytes(source.read_bytes())
    with Session() as s:
        s.load('test9')
        s.click(480,340);s.click(480,340)
        selected=state(s)
        s.click(540,340)
        single=state(s)
        report['selection']={'double_count':selected['selected_count'],
                             'single_count':single['selected_count'],
                             'single_indices':[u['index'] for u in single['selected']]}
        if selected['selected_count']!=4 or single['selected_count']!=1:
            raise RuntimeError('Selection regression')
        report['test9_run']=str(s.run)
    with Session() as s:
        s.load('test8');s.click(1040,25);time.sleep(.4)
        s.capture('grimoire-intro')
        s.click(195,132);time.sleep(.5)
        s.capture('grimoire-realm')
        s.result['realm_controls']=s.controls()
        # Inspect the known left-page black stripe using the native surface.
        with Image.open(s.run/'grimoire-realm.png') as im:
            dark=sum(max(im.getpixel((x,y)))<15 for y in range(180,645) for x in range(220,250))
        report['grimoire_dark_left_pixels']=dark
        if dark>200:raise RuntimeError('Grimoire left stripe remains')
        report['test8_run']=str(s.run)
    with Session() as s:
        s.load('test8');s.key(0x1b);time.sleep(.3)
        s.click(640,420);time.sleep(.3)
        s.capture('confirmation')
        controls=s.controls()
        report['confirmation_buttons']=[c['rect'] for c in controls if c['rect'][2]-c['rect'][0]==82 and c['rect'][3]-c['rect'][1]==32]
        if len(report['confirmation_buttons'])!=2 or not all(400<=r[0]<900 for r in report['confirmation_buttons']):
            raise RuntimeError('Confirmation buttons not centered')
        report['dialog_run']=str(s.run)
    report['status']='passed'
finally:
    for p,data in original.items():p.write_bytes(data)
    report['restored']=all(sha(p.read_bytes())==sha(data) for p,data in original.items())
    output=ROOT/'modernization/logs/wide169'/('followup-'+str(time.time_ns())+'.json')
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(output,report.get('status'),report['restored'])
