"""Owned background regression for native spell targeting and selection."""
import json
from pathlib import Path
import subprocess
import sys
import time

from hd_qol_background_session import STATE, no_game_running, send
from qol_telemetry import snapshot

ROOT = Path(__file__).resolve().parents[2]
report = {'checks': []}

def action(*args):
    out = subprocess.check_output([sys.executable, str(ROOT / 'modernization/tools/hd_qol_background_session.py'), *map(str,args)], cwd=ROOT, text=True)
    return json.loads(out)

def record(name, state):
    report['checks'].append({'name':name, 'state':state})
    (ROOT/'modernization/logs/hd-qol-casting.json').write_text(json.dumps(report,indent=2))

def selected(state, n=1):
    assert state['selected_count']==n and state['unit0']['selection']==n, state

def cancelled(state):
    selected(state)
    assert state['spellbox']['active_icon']==-1 and state['unit0']['pending_spell_index']==-1
    assert state['input_mode']==1

def run():
    no_game_running()
    layout=(ROOT/'modernization/config/qol-hotkeys.json').read_bytes()
    # This fixture gate deliberately uses the user's current layout without editing it.
    assert json.loads(layout)['bindings']=={
        'Q':{'tray':0,'slot':0}, 'W':{'tray':1,'slot':0},
        'E':{'tray':2,'slot':0}, 'R':{'tray':0,'slot':1}}
    try:
        action('start'); action('load-test7')
        record('select-wizard', action('key',0x5a))
        for key, icon in [('Q',0),('W',2),('E',3),('R',1)]:
            state=action('key',ord(key)); selected(state)
            assert state['spellbox']['active_icon']==icon and state['input_mode']==2
            record(key+'-target',state)
            state=action('right-click',560,420); cancelled(state);record(key+'-cancel',state)
        state=action('click',892,810);selected(state)
        assert state['spellbox']['active_icon']==0
        record('mouse-spell-selection',state)
        cancelled(action('right-click',560,420))
        # A drag must cancel before release and then finish native box selection.
        before=action('key',ord('W'))
        session=json.loads(STATE.read_text())
        before_bats=[u for u in before['units'] if u['owner']==1 and u['type']==15]
        send(session,0x200,(330<<16)|510);time.sleep(.08)
        send(session,0x201,(330<<16)|510);time.sleep(.2)
        send(session,0x200,(450<<16)|640);time.sleep(.3)
        state=snapshot(session['pid'])
        assert state['input_mode']==3 and state['unit0']['pending_spell_index']==-1
        assert state['spellbox']['active_icon']==-1
        record('drag-cancels-before-release',state)
        send(session,0x202,(450<<16)|640);time.sleep(.8)
        state=snapshot(session['pid']);selected(state)
        assert len([u for u in state['units'] if u['owner']==1 and u['type']==15])==len(before_bats)
        record('box-selection-completes-without-cast',state)
        before=action('key',ord('W'));selected(before)
        record('before-left-cast',before)
        before_bats=[u for u in before['units'] if u['owner']==1 and u['type']==15]
        session=json.loads(STATE.read_text())
        send(session,0x200,(420<<16)|600);time.sleep(.08)
        send(session,0x201,(420<<16)|600);time.sleep(1.5)
        state=snapshot(session['pid']);selected(state)
        assert len([u for u in state['units'] if u['owner']==1 and u['type']==15])==len(before_bats)
        assert state['input_mode']==2 and state['unit0']['pending_spell_index']==2
        record('held-left-does-not-cast',state)
        send(session,0x202,(420<<16)|600)
        for _ in range(60):
            state=snapshot(session['pid']);selected(state)
            bats=[u for u in state['units'] if u['owner']==1 and u['type']==15]
            if len(bats)>len(before_bats):break
            time.sleep(.1)
        else:raise AssertionError('Left cast did not produce a player bat')
        record('left-cast-created-bat',state)
        cancelled(action('right-click',600,420))
        record('test7-cleanup',action('stop'))
        action('start'); action('load-test2')
        state=action('click',536,341);selected(state);record('test2-select',state)
        before=state['unit0']['world']
        action('right-click',650,420)
        session=json.loads(STATE.read_text())
        for _ in range(30):
            state=snapshot(session['pid']);selected(state)
            if state['unit0']['world']!=before:break
            time.sleep(.1)
        else:raise AssertionError('Ordinary right move did not move the wizard')
        record('test2-right-move',state)
        report['passed']=True
    finally:
        record('cleanup',action('stop'))
        assert (ROOT/'modernization/config/qol-hotkeys.json').read_bytes()==layout
        report['layout_unchanged']=True
        (ROOT/'modernization/logs/hd-qol-casting.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'passed':report['passed'],'checks':len(report['checks'])}))

if __name__=='__main__':run()
