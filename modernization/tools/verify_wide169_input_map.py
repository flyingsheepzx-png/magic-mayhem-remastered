"""Reversible background regression for the next widescreen input/map candidate."""
from pathlib import Path
import json
import shutil
import time

from wide169_trial import ROOT, GAME, LAB, BUILD, Session, sha
from verify_hd60_runtime import read

INSTALLED = GAME / 'Chaos-Wide169-Trial.exe'
CANDIDATE = ROOT / 'modernization/build/Chaos-Wide169-Trial.exe'
STRIDE = 0xe4b


def units(s):
    base, capacity, count = s.i(0x6def58), s.i(0x6def5c), s.i(0x6df180)
    if not base or not 0 <= count <= capacity <= 1024:
        raise RuntimeError('Unknown unit table')
    return [dict(index=i, active=s.i(p+4), selected=s.i(p+0x68),
                 type=s.i(p+0xa8), owner=s.i(p+0x174),
                 pending=s.i(p+0x5e8), grid=[s.i(p+o) for o in (8,12,16)])
            for i in range(count) for p in [base+i*STRIDE] if s.i(p+4)]


def state(s):
    rows = units(s)
    return dict(mode=s.i(0x6903e8), icon=s.i(0x6a2dd0+0x1908),
                selected_count=s.i(0x6e984c), unit_count=s.i(0x6df180),
                selected=[r for r in rows if r['selected']],
                pending=[r for r in rows if r['pending'] >= 0])


def run():
    baseline=json.loads((ROOT/'modernization/current-baseline.json').read_text())['latest_development']['files']['game/Chaos-Wide169-Trial.exe']
    if sha(INSTALLED.read_bytes()) != baseline:
        raise RuntimeError('Unknown installed launcher')
    if not CANDIDATE.is_file():
        raise RuntimeError('Missing candidate launcher')
    backup = ROOT/'modernization/backups/wide169'/('input-map-verify-'+str(time.time_ns()))
    backup.mkdir(parents=True)
    shutil.copy2(INSTALLED, backup/INSTALLED.name)
    report = dict(installed_before=baseline, candidate=sha(CANDIDATE.read_bytes()), backup=str(backup))
    try:
        if sha(CANDIDATE.read_bytes())!=baseline:shutil.copy2(CANDIDATE, INSTALLED)
        with Session() as s:
            s.load('test9')
            report['test9_initial'] = state(s)
            base=s.i(0x6def58)
            report['unit0_grid']=[s.i(base+o) for o in (8,12,16)]
            picks=[]
            for x,y in ((630,315),(635,310),(650,312),(610,340),(640,320),(480,340)):
                s.message(0x200,x,y);time.sleep(.15)
                ptr=s.i(0x656600)
                picks.append(dict(mouse=[x,y],unit=(ptr-base)//STRIDE if base<=ptr<base+1024*STRIDE else -1,
                                  grid=[s.i(a) for a in (0x6c5488,0x6c5484,0x6cbb64)]))
            report['margin_picks']=picks
            # Blank ground followed by the hero sprite must remain distinguishable.
            s.click(610,340)
            report['blank'] = state(s)
            s.click(640,320)
            report['hero'] = state(s)
            s.click(480,340)
            report['first_creature'] = state(s)
            s.click(480,340)
            report['double_creature'] = state(s)
            s.capture('test9-double')
            # Reset selection to wizard, then use the first targeting spell.
            s.key(0x5a)
            time.sleep(.2)
            report['wizard_reselected'] = state(s)
            s.click(1049,695)
            report['spell_armed'] = state(s)
            s.message(0x200,1215,650)
            s.capture('test9-before-portrait-cast')
            hero=s.i(0x6def58)
            before=read(s.k,s.handle,hero,0x800)
            s.click(1215,650)
            report['portrait_release'] = state(s)
            time.sleep(2)
            report['portrait_settled'] = state(s)
            after=read(s.k,s.handle,hero,0x800)
            report['hero_changed_offsets']=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
            report['hero_changed_words']=[dict(offset=hex(i),before=int.from_bytes(before[i:i+4],'little',signed=True),
                                               after=int.from_bytes(after[i:i+4],'little',signed=True))
                                          for i in (0xb0,0xb4,0xbc,0xc0,0xc4,0xc8,0xe0,0x5e8,0x6bc,0x75c,0x768)]
            s.capture('test9-portrait-cast')
            orders=[]
            for x,y in ((700,400),(740,420),(540,420),(640,440)):
                s.message(0x200,x,y);time.sleep(.15)
                grid=[s.i(a) for a in (0x6c5488,0x6c5484,0x6cbb64)]
                s.click(x,y,True);time.sleep(.15)
                orders.append(dict(mouse=[x,y],hover_grid=grid,
                                   move_goal=[s.i(base+o) for o in (0x96b,0x96f,0x973)]))
            report['move_grid_checks']=orders
            report['test9_log'] = str(s.run)
        with Session() as s:
            s.load('test8')
            report['test8_initial'] = state(s)
            for j,(x,y) in enumerate(((760,224),(570,270),(450,190),(880,490))):
                s.message(0x200,x,y)
                time.sleep(.25)
                s.capture('test8-hover-'+str(j))
            report['test8_log'] = str(s.run)
        with Session() as s:
            s.load('test7');s.key(0x5a);time.sleep(.2)
            before=units(s)
            s.key(ord('W'));time.sleep(.2)
            s.message(0x200,700,400);time.sleep(.15)
            grid=[s.i(a) for a in (0x6c5488,0x6c5484,0x6cbb64)]
            s.click(700,400)
            for _ in range(60):
                after=units(s)
                new=[u for u in after if u['index'] not in {v['index'] for v in before}]
                if new:break
                time.sleep(.1)
            report['spell_grid_check']=dict(mouse=[700,400],hover_grid=grid,new_units=new)
            s.capture('test7-summon');report['test7_log']=str(s.run)
    finally:
        shutil.copy2(backup/INSTALLED.name, INSTALLED)
        report['installed_restored'] = sha(INSTALLED.read_bytes()) == baseline
        output = ROOT/'modernization/logs/wide169'/('input-map-verify-'+str(time.time_ns())+'.json')
        output.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(output,flush=True)
        if not report['installed_restored']:
            raise RuntimeError('Installed launcher restoration failed')


if __name__ == '__main__':
    run()
