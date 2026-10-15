import json,time,ctypes
from pathlib import Path
import hd_qol_background_session as m
from qol_telemetry import snapshot
s=json.loads(m.STATE.read_text()); initial=snapshot(s['pid'])
if initial.get('unit0',{}).get('group')!=-1 or initial['unit0']['grid']!=[66,48,6]:
 raise RuntimeError('Requires test2 with unit0 on original grid and no group assignment')
u,h=m.window(s['pid'])
u.PostMessageW.argtypes=[m.wintypes.HWND,m.wintypes.UINT,m.wintypes.WPARAM,m.wintypes.LPARAM]
def clear():
 u.PostMessageW(h,0x100,0x30,1);time.sleep(.04);u.PostMessageW(h,0x101,0x30,0xc0000001);time.sleep(.04)
rows=[]
for y in range(325,436,10):
 for x in range(510,611,10):
  clear();c=(y<<16)|x
  for msg in (0x200,0x201,0x202):m.send(s,msg,c);time.sleep(.075 if msg==0x201 else .01)
  state=snapshot(s['pid']);rows.append({'x':x,'y':y,'selected':state['unit0']['selection'],'count':state['selected_count'],'cursor':state['cursor_draw_top_left']})
report={'engine':state['engine_sha256'],'fixture':'test2','unit_grid':state['unit0']['grid'],'rows':rows}
Path('modernization/logs/test2-native-pick-grid.json').write_text(json.dumps(report,indent=2))
for y in range(325,436,10):print(y,''.join('#' if r['selected'] else '.' for r in rows if r['y']==y))
