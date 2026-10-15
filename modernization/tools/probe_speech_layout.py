import os,struct,json
from pathlib import Path
from wide169_trial import Session,ROOT
from verify_hd60_runtime import read
from compare_hd_baseline import baseline_identity
baseline_identity()
os.environ['MM_ALLOW_NATIVE_CLIENT']='1';os.environ['MM_ALLOW_SCALED_CLIENT']='1'
lines=(ROOT/'modernization/build/occluded-units-v3/repath.map').read_text().splitlines()
def addr(name):return int(next(x for x in lines if '?'+name+'@@' in x).split()[2],16)
def main():
 with Session() as s:
  s.load('test14')
  import time
  s.click(920,450);time.sleep(.8);s.capture('tutorial')
  data=[dict(index=j,rect=[s.i(0x6a2dd0+0xfc+j*0xc6+o) for o in (0x11,0x15,0x19,0x1d)],fields={hex(o):s.i(0x6a2dd0+0xfc+j*0xc6+o) for o in (0x3d,0xb5,0xb9)}) for j in range(5)]
  (s.run/'icons.json').write_text(json.dumps(data,indent=2));print(data,flush=True)
  s.click(1004,692);time.sleep(.8);s.capture('spell-clicked')
  s.result['spell_click']={'mode':s.i(0x6903e8),'selected_icon':s.i(0x6a2dd0+0x1908)}
  assert s.i(s.i(0x6def58)+4), 'No loaded unit'
  print(s.run,flush=True)

if __name__=='__main__':
 prefs=ROOT/'game-wide169/CFG/prefs.cfg'
 original=prefs.read_bytes();stat=prefs.stat()
 backup=ROOT/'modernization/logs/occlusion-prefs-backup.cfg';backup.write_bytes(original)
 try:
  prefs.write_bytes(original.replace(b'PlayFMV=TRUE',b'PlayFMV=FALSE'))
  main()
 finally:
  prefs.write_bytes(original);os.utime(prefs,ns=(stat.st_atime_ns,stat.st_mtime_ns))
