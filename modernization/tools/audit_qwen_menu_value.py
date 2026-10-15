"""Capture baseline, Qwen and plain-upscale menu in isolated mixed UI v4."""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import time
from PIL import Image, ImageChops, ImageStat, ImageFilter
from compare_hd_baseline import CaptureSession, baseline_identity, sha
from wide169_build import ROOT

REL = 'Interface/MainScreen/800x600/Main Menu 800-600.JPG'
PNG = 'Interface/MainScreen/800x600/Main Menu 800-600.png'
PACKAGE = ROOT / 'modernization/playtests/mixed-ui-v4'
QUEUE = ROOT / 'modernization/assets/hd/hd-queue.json'
EXPECTED_CANDIDATE = '5d1b68e63a712e73886f9a5c803f68d16e608aaf583214e89d07eb8c564ee8ee'

def framed_jpeg(image: Image.Image) -> bytes:
    canvas = Image.new('RGB', (2560, 1440))
    canvas.paste(image.convert('RGB'), (320, 0))
    buffer = io.BytesIO()
    canvas.save(buffer, 'JPEG', quality=100, subsampling=0)
    return buffer.getvalue()

def edge(image: Image.Image) -> float:
    return ImageStat.Stat(image.convert('L').filter(ImageFilter.FIND_EDGES)).stddev[0]

def main():
    baseline_identity()
    manifest_path = PACKAGE / 'manifest.json'
    asset_path = PACKAGE / 'game-wide169' / REL
    original_asset = asset_path.read_bytes()
    original_manifest = manifest_path.read_bytes()
    manifest = json.loads(original_manifest)
    key = 'game-wide169/' + REL
    if sha(asset_path) != EXPECTED_CANDIDATE or manifest['files'].get(key,EXPECTED_CANDIDATE) != EXPECTED_CANDIDATE:
        raise RuntimeError('Unknown menu candidate')
    if any(sha(PACKAGE / name) != digest for name,digest in manifest['files'].items()):
        raise RuntimeError('Candidate manifest mismatch')
    queue = json.loads(QUEUE.read_text(encoding='utf-8'))
    row = next(record for record in queue['records'] if record['source'] == REL)
    source = ROOT / 'modernization/assets/hd/source-original' / REL
    qwen = ROOT / 'modernization/assets/hd/pack' / PNG
    if row['status'] != 'done' or sha(source) != row['source_sha256'] or sha(qwen) != row['output_sha256']:
        raise RuntimeError('Source or Qwen output identity mismatch')
    with Image.open(source) as s, Image.open(qwen) as q:
        if s.size != (800,600) or q.size != (1920,1440):
            raise RuntimeError('Wrong image geometry')
        qwen_bytes = framed_jpeg(q)
        plain_bytes = framed_jpeg(s.resize((1920,1440),Image.Resampling.LANCZOS))
    if qwen_bytes != original_asset:
        raise RuntimeError('Candidate is not the verified Qwen output')
    out = ROOT / 'modernization/assets/hd/qwen-value-audits' / str(time.time_ns())
    out.mkdir(parents=True)
    for name in ('baseline-run','qwen-run','plain-run'):
        (out/name).mkdir()
    (out/'rollback-menu.JPG').write_bytes(original_asset)
    (out/'rollback-manifest.json').write_bytes(original_manifest)
    try:
        with CaptureSession('baseline',out/'baseline-run','mixed-ui-v4') as session:
            session.shot('menu')
            session.require_visible('menu')
        with CaptureSession('hd',out/'qwen-run','mixed-ui-v4') as session:
            session.shot('menu-qwen')
            session.require_visible('menu-qwen')
        asset_path.write_bytes(plain_bytes)
        manifest['files'][key] = hashlib.sha256(plain_bytes).hexdigest()
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        with CaptureSession('hd',out/'plain-run','mixed-ui-v4') as session:
            session.shot('menu-plain')
            session.require_visible('menu-plain')
    finally:
        asset_path.write_bytes(original_asset)
        manifest_path.write_bytes(original_manifest)
    if asset_path.read_bytes()!=original_asset or manifest_path.read_bytes()!=original_manifest:
        raise RuntimeError('Asset rollback failed')
    for run,label in (('baseline-run','baseline'),('qwen-run','hd'),('plain-run','hd')):
        capture=json.loads((out/run/label/'capture.json').read_text(encoding='utf-8'))
        if not capture.get('restored') or capture.get('error'):
            raise RuntimeError('Game-session rollback failed: '+run)
    if any(sha(PACKAGE / name) != digest for name,digest in
           json.loads(original_manifest)['files'].items()):
        raise RuntimeError('Candidate package changed after rollback')
    paths = {
        'baseline':out/'baseline-run/baseline/menu-2560x1440.png',
        'qwen':out/'qwen-run/hd/menu-qwen-2560x1440.png',
        'plain':out/'plain-run/hd/menu-plain-2560x1440.png',
    }
    with Image.open(paths['baseline']) as b,Image.open(paths['qwen']) as q,Image.open(paths['plain']) as p:
        images=[b.convert('RGB'),q.convert('RGB'),p.convert('RGB')]
        triple=Image.new('RGB',(7680,1440))
        for i,image in enumerate(images):triple.paste(image,(2560*i,0))
        triple.save(out/'menu-baseline-qwen-plain-7680x1440.png')
        region=(320,0,2240,1440)
        q_crop=images[1].crop(region);p_crop=images[2].crop(region)
        difference=ImageChops.difference(q_crop,p_crop)
        stats=ImageStat.Stat(difference)
        report={
            'source':REL,'source_sha256':row['source_sha256'],
            'qwen_png_sha256':row['output_sha256'],
            'qwen_runtime_sha256':EXPECTED_CANDIDATE,
            'plain_runtime_sha256':hashlib.sha256(plain_bytes).hexdigest(),
            'output_size':[2560,1440], 'content_box':list(region),
            'game_captures':{name:str(path) for name,path in paths.items()},
            'mean_abs_rgb_difference':round(sum(stats.mean)/3,3),
            'qwen_edge_stddev':round(edge(q_crop),3),
            'plain_edge_stddev':round(edge(p_crop),3),
            'runtime_restored':True,
            'status':'captured-pending-visual-verdict',
        }
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(out)

if __name__=='__main__':main()
