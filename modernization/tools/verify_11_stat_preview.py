"""Compare actual save12 pixels against exact RGB565 colour/gray state strips."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
import build_11_stat_preview as b

def pack(a):return ((a[:,:,0]>>3)<<11)|((a[:,:,1]>>2)<<5)|(a[:,:,2]>>3)
def main():
 evidence={};fixtures=[]
 for mode in ['before','after']:
  run=b.b.ROOT/'modernization/logs/remastered-ui'/('save12-stat-preview-'+mode)
  capture=json.loads((run/'run/capture.json').read_text());assert capture['status']=='captured' and capture['restored'] and not capture['cleanup_errors']
  fixtures.append(capture['fixture_sha256']);root=run/'package/runtime'/b.REL/'800x600' if mode=='before' else b.OUT/'assets'
  stats={}
  for name,y in [('Mana Bar',552),('Health Bar',672),('Control Limit Bar',792)]:
   art=np.array(Image.open(root/(name+'.PNG')).convert('RGB'),dtype=np.uint16);w=art.shape[1]//2;h=art.shape[0]
   target=pack(art);gray=target[:,w:];colour=target[:,:w]
   mask=~b.sr.keys(Image.fromarray(art[:,:w].astype(np.uint8)));valid=mask.sum(0)>10;rows=[]
   for label in ['initial','plus1','plus2','plus3']:
    im=np.array(Image.open(run/'run'/('character-'+label+'-native.png')).convert('RGB'),dtype=np.uint16)
    assert im.shape==(1440,2560,3)
    tile=pack(im[y:y+h,968:968+w]);sim=((tile==gray)&mask).sum(0)/np.maximum(1,mask.sum(0));match=np.where((sim>.95)&valid)[0]
    cs=((tile==colour)&mask).sum(0)/np.maximum(1,mask.sum(0));cm=np.where((cs>.95)&valid)[0]
    rows.append(dict(label=label,colour_end=int(cm.max()),preview_start=int(match.min()) if len(match) else None,preview_end=int(match.max()) if len(match) else None,preview_columns=len(match)))
   stats[name]=rows
  evidence[mode]=stats
 assert fixtures[0]==fixtures[1]==b.b.sha(b.base.DEST/'runtime/Save/12.sav')
 assert [r['preview_columns'] for r in evidence['before']['Mana Bar']]==[0,7,7,7]
 for name,rows in evidence['after'].items():
  assert [r['preview_columns'] for r in rows]==[0,21,42,63]
  assert len({r['colour_end'] for r in rows})==1
  for i,row in enumerate(rows[1:],1):assert row['preview_start']==rows[0]['colour_end']+1 and row['preview_end']==rows[0]['colour_end']+i*21
 v=json.loads((b.OUT/'verification.json').read_text());v.update(save12_verified=True,fixture_sha256=fixtures[0],runtime_pixels=evidence,runtime_acceptance='isolated save12 sequential increments and cancellation passed; user acceptance pending')
 b.b.write(b.OUT/'verification.json',v);print('Save12: before mana preview7/7/7; after all3bars21/42/63 pixels; saves restored')

if __name__=='__main__':main()
