"""Owned, resumable FullReadable map jobs via authenticated LocalModelManager."""
import os
from pathlib import Path
import argparse,base64,hashlib,io,json,time,urllib.request,urllib.parse,sys
import numpy as np
from PIL import Image,ImageFilter,ImageDraw
from realm_portal_art import PORTALS,composite_portal
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'modernization/assets/hd/fullreadable-realms-20261002'
RT=Path('D:/Games/Magic&Mayham_Remastered_1.1/runtime')
BASE='http://127.0.0.1:8790'
HASHES={'Medieval':'b67c1f28a992ca9b2ad70cda6b7a835b1153d04d6ca947d9a1cabb9c1644fbfa','Greek':'ba2e7b22fc9e0d1a3d84dbc18e4dddf661d1f4473014631a641108ce473913ec'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def request(route,payload=None,key=None,raw=False):
    token=json.loads(Path(os.environ['MM_LOCAL_MODEL_CREDENTIAL']).read_text(encoding='utf-8'))['token']
    headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
    if key:headers['Idempotency-Key']=key
    req=urllib.request.Request(BASE+route,headers=headers,data=None if payload is None else json.dumps(payload).encode())
    with urllib.request.urlopen(req,timeout=45) as r:return r.read() if raw else json.load(r)
def run(world):
    dest=OUT/world;dest.mkdir(parents=True,exist_ok=True);log=dest/'job.json'
    source=ROOT/f'modernization/assets/hd/source-original/Interface/RealmViewer/800x600/{world}_Map.bmp'
    assert sha(source)==HASHES[world],'Unknown original'
    image=Image.open(source).convert('RGB');buf=io.BytesIO();image.save(buf,format='PNG')
    old=RT/f'Interface/RealmViewer/800x600/{world}_Map.PNG'
    settings=json.loads((ROOT/'modernization/assets/hd/quality-review-1.1/model-trials/02-full-readable-call.json').read_text(encoding='utf-8'))['request']
    settings['prompt']=settings['prompt'].replace('Celtic realm',world+' realm')
    settings['nickname']='MM 1.1 '+world+' FullReadable 20261002'
    # Same accepted seed/settings; reference map distinguishes each chapter.
    if log.exists():record=json.loads(log.read_text(encoding='utf-8'))
    else:
        status=request('/workbench/api/keyframe2/status');engine=status.get('engines',{}).get('qwen21',{})
        assert engine.get('ok') and engine.get('assets_ready'),'Qwen not ready'
        payload=dict(settings,reference_images=['data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()])
        job=request('/workbench/api/keyframe2/jobs',payload,key='mm-fullreadable-20261002-'+world)['job']
        record={'manager_job_id':job['id'],'source_sha256':sha(source),'installed_before_sha256':sha(old),'request':settings,'observations':[]}
        save(log,record)
    print('Owned job',world,record['manager_job_id'],flush=True)
    if not (dest/'raw.png').exists():
        start=time.monotonic();last=None
        while True:
            job=request('/workbench/api/keyframe2/jobs/'+record['manager_job_id'])['job']
            state=(job.get('status'),job.get('phase_code') or job.get('phase'))
            if state!=last:
                print(state,flush=True);record['observations'].append(list(state));save(log,record);last=state
            if state[0] in ['completed','failed','canceled','cancelled','interrupted']:break
            if time.monotonic()-start>2400:
                request('/workbench/api/keyframe2/jobs/'+record['manager_job_id']+'/cancel',{});raise TimeoutError('Owned job canceled after deadline')
            time.sleep(3)
        record['terminal_status']=state[0];save(log,record)
        assert state[0]=='completed',str(job.get('error') or state)
        assert job.get('engine')=='qwen21' and job.get('prompt')==settings['prompt'],'Wrong job identity'
        media=next(s['primary'] for s in job['sequences'] if s.get('primary'))
        url=urllib.parse.urlparse(urllib.parse.urljoin(BASE,media['url']))
        assert url.netloc=='127.0.0.1:8790' and url.path.startswith('/workbench/api/')
        raw=request(url.path+('?' +url.query if url.query else ''),raw=True)
        assert raw.startswith(b'\x89PNG\r\n\x1a\n');(dest/'raw.png').write_bytes(raw)
    gen=Image.open(dest/'raw.png').convert('RGB');assert gen.size==(2400,1792)
    target=gen.resize((1920,1440),Image.Resampling.LANCZOS);target.save(dest/'target-1920x1440.png')
    base=Image.new('RGB',(2560,1440));base.paste(target,(320,0));rgb=np.array(base)
    rel=f'Interface/RealmViewer/800x600/{world}_Map.PNG';p=dest/'runtime'/rel;p.parent.mkdir(parents=True,exist_ok=True);base.save(p)
    records=[{'path':rel,'sha256':sha(p),'before_sha256':record['installed_before_sha256']}]
    masks=sorted((RT/'Interface/RealmViewer/800x600').glob(world+'_*'))
    masks=[m for m in masks if '_border_' in m.name.lower() and m.suffix.lower()=='.pcx']
    assert len(masks)==(17 if world=='Medieval' else 14)
    for mask in masks:
        region=int(mask.stem.split('_')[-1]);original=Image.open(mask).convert('RGB');assert original.size==(800,600)
        m=Image.fromarray((np.any(np.array(original)!=[0,0,255],axis=2)*255).astype('uint8')).resize((1920,1440),Image.Resampling.LANCZOS)
        coverage=Image.new('L',base.size);coverage.paste(m,(320,0));a=np.array(coverage,dtype=np.float32)/255
        rim=Image.new('L',base.size);rim.paste(m.filter(ImageFilter.MinFilter(9)),(320,0));edge=np.clip(a-np.array(rim,dtype=np.float32)/255,0,1)
        colour=rgb.astype(np.float32);enhanced=np.minimum(colour*1.10+np.array([3,4,0]),255)
        result=colour+(enhanced-colour)*a[:,:,None];result=result*(1-edge[:,:,None]*.6)+np.array([208,220,55])*edge[:,:,None]*.6
        result=np.rint(result).clip(0,255).astype('uint8');outside=a==0
        if (world,region) in PORTALS:
            portal,coverage=composite_portal(base,original);result=np.array(portal);outside=np.array(coverage)==0
        assert np.array_equal(result[outside],rgb[outside]);assert not result[:,:320].any() and not result[:,2240:].any()
        rel=f'Interface/RealmViewer/hd-selected/{world}_{region:02d}.PNG';p=dest/'runtime'/rel;p.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(result).save(p)
        records.append({'path':rel,'sha256':sha(p),'before_sha256':sha(RT/rel),'mask_sha256':sha(mask),'outside_exact':True})
    compare=Image.new('RGB',(1920,780));draw=ImageDraw.Draw(compare)
    for n,(label,img) in enumerate([('Previous',Image.open(old).crop((320,0,2240,1440))),('Qwen FullReadable',target)]):
        compare.paste(img.resize((960,720)),(n*960,40));draw.text((n*960+20,12),label,fill='white')
    compare.save(dest/'comparison.png')
    save(dest/'verification.json',{'world':world,'raw_sha256':sha(dest/'raw.png'),'target_sha256':sha(dest/'target-1920x1440.png'),'raw_size':gen.size,'canvas_size':base.size,'content_rect':[320,0,2240,1440],'records':records,'selected_states':len(masks),'portal_art_preserved':True})
    print('Verified base and states',world,len(masks),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('world',choices=list(HASHES));run(p.parse_args().world)

