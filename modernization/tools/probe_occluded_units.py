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
  s.load('test13')
  code=read(s.k,s.handle,0x4fd552,5);delta=0x4fd557+struct.unpack('<i',code[1:])[0]-addr('before_hook')
  def blob(name,n):return read(s.k,s.handle,addr(name)+delta,n)
  count=struct.unpack('<i',blob('command_count',4))[0]
  commands=blob('saved',count*36);owners=struct.unpack('<'+'i'*count,blob('owners',4*count));bodies=blob('body_commands',count)
  hero=s.i(0x6def58)
  rows=[]
  for j in range(count):
   if owners[j]==0:
    c=commands[j*36:(j+1)*36];sprite=struct.unpack_from('<I',c,4)[0]
    rows.append(dict(index=j,body=bodies[j],command=list(struct.unpack('<9i',c)),shorts=list(struct.unpack_from('<2h',c,28)),sprite=list(struct.unpack('<10i',read(s.k,s.handle,sprite,40)))))
  out=dict(count=count,bodies=sum(bodies),hero=rows,gates={x:list(blob(x,1)) for x in ['captured','replay_enabled','occluded_units_enabled']},unit={hex(o):s.i(hero+o) for o in [4,0xe4,8,12,16]},delta=delta,native={hex(a):s.i(a) for a in [0x5e1404,0x6c4e3c,0x6e1f88]})
  (s.run/'occlusion.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))

if __name__=='__main__':
 prefs=ROOT/'game-wide169/CFG/prefs.cfg'
 original=prefs.read_bytes();stat=prefs.stat()
 backup=ROOT/'modernization/logs/occlusion-prefs-backup.cfg';backup.write_bytes(original)
 try:
  prefs.write_bytes(original.replace(b'PlayFMV=TRUE',b'PlayFMV=FALSE'))
  main()
 finally:
  prefs.write_bytes(original);os.utime(prefs,ns=(stat.st_atime_ns,stat.st_mtime_ns))
