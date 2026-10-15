from pathlib import Path
import json, subprocess, sys
from importlib.util import spec_from_file_location, module_from_spec
root=Path(__file__).resolve().parents[2]
spec=spec_from_file_location('hdq',root/'modernization/tools/hd_qol_background_session.py')
m=module_from_spec(spec);spec.loader.exec_module(m)
state=json.loads(m.STATE.read_text())
config=root/'modernization/config/qol-hotkeys.json'
def send_key(k):
    u,h=m.window(state['pid']);u.PostMessageW.argtypes=[m.wintypes.HWND,m.wintypes.UINT,m.wintypes.WPARAM,m.wintypes.LPARAM]
    u.PostMessageW(h,0x100,ord(k),1);m.time.sleep(.08);u.PostMessageW(h,0x101,ord(k),0xc0000001);m.time.sleep(.08)
def move(x,y):
    m.send(state,0x200,(y<<16)|x);m.time.sleep(.08)
def bindings():return json.loads(config.read_text(encoding='utf-8'))['bindings']
if bindings():raise RuntimeError('Start a fresh isolated test6 session with an empty backed-up layout before running this test')
results=[]
move(315,760)
for k in 'QWERASDFZXCV':
    send_key(k)
    expected={k:{'tray':0,'slot':0}}
    assert bindings()==expected,(k,bindings())
    results.append(k)
move(315,640);send_key('V')
assert bindings()=={'V':{'tray':0,'slot':1}}
move(185,760);send_key('V')
assert bindings()=={'V':{'tray':1,'slot':0}}
move(55,760);send_key('V')
assert bindings()=={'V':{'tray':2,'slot':0}}
move(315,640);send_key('Q')
assert bindings()=={'V':{'tray':2,'slot':0},'Q':{'tray':0,'slot':1}}
move(700,500);send_key('W')
assert bindings()=={'V':{'tray':2,'slot':0},'Q':{'tray':0,'slot':1}}
move(55,760)
u,h=m.window(state['pid']);u.PostMessageW(h,0x100,0x2e,1);m.time.sleep(.08);u.PostMessageW(h,0x101,0x2e,0xc0000001);m.time.sleep(.08)
assert bindings()=={'Q':{'tray':0,'slot':1}}
report={'all_12_keys_bound':results,'duplicate_transfer_trays':[0,1,2],'outside_hover_unchanged':True,'delete_clears':True,'final':bindings()}
(root/'modernization/logs/hd-qol-live-binding.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
