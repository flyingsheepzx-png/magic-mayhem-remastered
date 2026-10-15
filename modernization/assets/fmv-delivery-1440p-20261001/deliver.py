"""CPU-only, resumable H.264 delivery. Never submits inference or edits runtime."""
import argparse, hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OLD=Path('D:/AI/LocalModelManager/media/magic-mayhem-fmv-20260928')
SRC=Path('D:/Games/MagicMayham-backups/original-fmv-indeo-20260928/FMV')
FF='E:/AI/LosslessCut/resources/ffmpeg.exe'
FP='E:/AI/LosslessCut/resources/ffprobe.exe'
MAN=ROOT/'manifest.json'

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def save(d):
 t=MAN.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8');t.replace(MAN)
def probe(p,frames=False):
 cmd=[FP,'-v','error','-show_streams','-show_format','-of','json']
 if frames:cmd+=['-count_frames']
 return json.loads(subprocess.check_output(cmd+[str(p)],timeout=300))
def times(p):
 d=json.loads(subprocess.check_output([FP,'-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(p)],timeout=300))
 return [float(x['best_effort_timestamp_time']) for x in d['frames']]
def pcm(p):
 return subprocess.check_output([FF,'-v','error','-i',str(p),'-map','0:a:0','-c:a','pcm_s16le','-f','hash','-hash','sha256','-'],timeout=300).decode().strip()
def run(cmd,log):
 with log.open('w',encoding='utf-8') as f:subprocess.run(cmd,stdout=f,stderr=f,check=True,timeout=7200)
def deliver(name,raw=None,restore=False):
 m=json.loads(MAN.read_text(encoding='utf-8')) if MAN.exists() else {'policy':{'target':[2560,1440],'video':'H.264 libx264 CRF18 slow yuv420p','audio':'MP4 AAC192k + MKV original PCM','runtime_acceptance':'pending actual game playback'},'films':{}}
 source=SRC/f'{name}.avi'
 if raw: inp=Path(raw);crop=False
 elif name in ('Medieval','Intro1'):inp=OLD/f'1920x1440/masters/{name}.mkv';crop=True
 else:raise ValueError('explicit input required')
 old=m['films'].get(name,{})
 if old.get('verified') and all(Path(old[k]).exists() and sha(old[k])==old[k+'_sha256'] for k in ('mp4','master')):
  print('REUSE_VERIFIED',name,flush=True);return
 row={'input':str(inp),'input_sha256':sha(inp),'original':str(source),'original_sha256':sha(source),'method':'existing SeedVR2 3x + Lanczos 4/3 delivery' if crop else 'explicit supplied restoration/mixed input','crop_old_bars':crop}
 m['films'][name]=row;save(m)
 vf=('crop=1920:1080:0:180,' if crop else '')+'scale=2560:1440:flags=lanczos,setsar=1'
 if restore:
  ts=times(source);expr='N/16'
  if ts[0]:expr+=f'+{ts[0]}'
  for i in range(1,len(ts)):
   extra=ts[i]-ts[i-1]-1/16
   if abs(extra)>1e-6:expr+=f'+gte(N,{i})*{extra:.8f}'
  vf+=f",settb=1/16000,setpts='16000*({expr})'"
 mp4=ROOT/f'{name}.mp4';master=ROOT/f'{name}-original-PCM.mkv'
 cmd=[FF,'-hide_banner','-v','warning','-y','-i',str(inp),'-i',str(source),'-map','0:v:0','-map','1:a:0','-vf',vf,'-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','22050','-fps_mode','passthrough','-enc_time_base','1:16000','-movflags','+faststart',str(mp4)]
 row['encode_command']=cmd;save(m);print('ENCODING',name,flush=True);run(cmd,ROOT/f'{name}-encode.log')
 run([FF,'-v','warning','-y','-i',str(mp4),'-i',str(source),'-map','0:v:0','-map','1:a:0','-c','copy',str(master)],ROOT/f'{name}-mux.log')
 p=probe(mp4,True);v=next(s for s in p['streams'] if s['codec_type']=='video');assert (v['width'],v['height'],v['codec_name'])==(2560,1440,'h264')
 expected=times(source) if name in ('Medieval','Intro1','intro0') else times(inp)
 actual=times(mp4);assert len(actual)==len(expected),(len(actual),len(expected))
 err=max(abs(a-b) for a,b in zip(actual,expected));assert err<0.0011,err
 assert abs(float(p['format']['duration'])-float(probe(source)['format']['duration']))<0.15
 run([FF,'-v','error','-i',str(mp4),'-f','null','-'],ROOT/f'{name}-decode.log')
 assert pcm(master)==pcm(source)
 assert sha(source)==row['original_sha256'] and sha(inp)==row['input_sha256']
 for k,pth in [('mp4',mp4),('master',master)]:row[k]=str(pth);row[k+'_sha256']=sha(pth)
 row.update(verified=True,frames=len(actual),max_timestamp_error_seconds=err,duration=p['format']['duration'],pcm_sha256=pcm(master),bytes=mp4.stat().st_size)
 save(m);print('VERIFIED',name,len(actual),err,flush=True)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('names',nargs='+');a.add_argument('--input');a.add_argument('--restore-timing',action='store_true');o=a.parse_args()
 for n in o.names:deliver(n,o.input,o.restore_timing)
