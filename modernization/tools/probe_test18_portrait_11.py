"""Owned test18 teammate portrait input and read-only spell/unit evidence."""
import argparse,ctypes,time,os
import compare_remastered_ui_11 as c
from verify_wide169_input_map import state

def run(name):
 ctypes.windll.user32.SetProcessDPIAware();p=c.CANDIDATE
 identity=c.verify_package(p,'1.1',c.sha(p/'manifest.json'))
 out=c.ROOT/'modernization/logs/remastered-ui'/name;out.mkdir(exist_ok=False)
 s=c.session_class()(identity,p/'runtime',out/'1.1',80)
 with s:
  f=s.lab/'Save/test18.sav';stamp=time.time_ns();os.utime(f,ns=(stamp,stamp))
  s.click_base(640,456);time.sleep(.7)
  rect=next(x['rect'] for x in s.controls() if x['vtable']=='0x5c6db8')
  height=s.i(s.i(0x656680)+16)+2;x=(rect[0]+rect[2])//2;y=rect[1]+height//2
  for ev in [0x200,0x201,0x202]:s.message(ev,x,y);time.sleep(.09)
  s.click_base(328,666)
  deadline=time.monotonic()+15
  while time.monotonic()<deadline:
   if any(x['vtable']=='0x5c6e38' for x in s.controls()) and s.i(0x6df180)>0:break
   time.sleep(.1)
  else:raise RuntimeError('Battle not ready')
  time.sleep(3)
  s.key(0x5a);time.sleep(.2)
  rows=s.controls()
  for row in rows:
   ptr=int(row['pointer'],16)
   for off in [0x25,0x29]:
    a=s.i(ptr+off);row[hex(off)]=hex(a)
    if 0x10000<a<0x7fffffff:
     try:
      table=s.i(a);row[hex(off)+'_vtable']=hex(table)
      row[hex(off)+'_member']=[hex(s.i(a+j)) for j in [4,8,12]]
      if 0x400000<=table<0x600000:row[hex(off)+'_callback']=hex(s.i(table))
     except OSError:pass
  c.write_json(out/'controls.json',rows)
  s.result['initial']=state(s)
  s.result['spell_icons']=[dict(index=i,spell=s.i(0x6a2dd0+0xfc+i*0xc6+0xb5),disabled=s.i(0x6a2dd0+0xfc+i*0xc6+0x3d)) for i in range(min(24,s.i(0x6a2dd0+0x1518)))]
  portraits=sorted([r for r in rows if r['vtable']=='0x5c5c2c'],key=lambda r:r['rect'][1])
  assert len(portraits)==2
  row=portraits[1];target=s.i(int(row['pointer'],16)+0x89);base=s.i(0x6def58)
  assert base<=target<base+s.i(0x6def5c)*0xe4b and (target-base)%0xe4b==0
  caster=s.i(0x6a2dd0+0x18ec);assert caster==base
  rect=row['rect'];pos=((rect[0]+rect[2])//2,(rect[1]+rect[3])//2)
  def sample():return dict(state=state(s),mana=s.i(caster+0xec),target_hp=s.i(target+0xe4),cursor=s.i(0x5e04c8),target_index=(target-base)//0xe4b)
  casts=[]
  for right in [False,True]:
   s.key(0x5a);s.key(ord('W'));time.sleep(.2)
   pending=s.i(caster+0x5e8);assert 0<=pending<30 and s.i(caster+0x570+4*pending)==41
   s.message(0x200,pos[0]*2,pos[1]*2);time.sleep(.25)
   before=sample();s.click_base(*pos,right=right);time.sleep(1)
   casts.append(dict(right=right,before=before,after=sample(),portrait=row))
  s.result['casts']=casts
  s.shot('battle',False)
 print(out)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);a=p.parse_args();run(a.name)
