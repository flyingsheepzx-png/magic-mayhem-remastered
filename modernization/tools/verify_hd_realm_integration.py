"""Reversible in-game check of prepared Qwen Celtic realm art."""
import hashlib
import io
import json
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parent))
from wide169_trial import LAB,ROOT,Session,sha

QUEUE=ROOT/'modernization/assets/hd/hd-queue.json'
PACK=ROOT/'modernization/assets/hd/pack'
NAMES=('Celtic_Map.bmp','Celtic_border_05.pcx','Celtic_border_06.pcx')


def main():
    queue=json.loads(QUEUE.read_text(encoding='utf-8'))
    records={Path(r['source']).name.lower():r for r in queue['records']}
    folder=LAB/'Interface/RealmViewer/800x600'
    originals={name:(folder/name).read_bytes() for name in NAMES}
    converted={}
    for name in NAMES:
        row=records[name.lower()]
        if row['status']!='done':raise RuntimeError('Qwen output unfinished: '+name)
        png=PACK/row['output']
        if sha(png.read_bytes())!=row['output_sha256']:
            raise RuntimeError('Qwen output hash mismatch: '+name)
        with Image.open(png) as image:
            if image.format!='PNG' or image.size!=(1920,1440):
                raise RuntimeError('Unexpected Qwen format: '+name)
            if name.lower().endswith('.bmp'):
                out=Image.new('RGB',(1280,720),(0,0,0))
                out.paste(image.convert('RGB').resize((960,720),Image.Resampling.LANCZOS),(160,0))
                buf=io.BytesIO();out.save(buf,'BMP')
            else:
                source=Image.open(io.BytesIO(originals[name]))
                if source.mode!='P' or source.size!=(800,600):
                    raise RuntimeError('Unknown border palette/size: '+name)
                key=source.getpixel((0,0))
                mask=source.point(lambda value: 255 if value==key else 0).convert('L')
                out=image.convert('RGB').resize((800,600),Image.Resampling.LANCZOS)
                out.paste((0,0,255),(0,0,800,600),mask)
                buf=io.BytesIO();out.save(buf,'PCX')
        converted[name]=buf.getvalue()
    report={'source_queue_sha256':sha(QUEUE.read_bytes()),
            'art':{name:dict(original=sha(originals[name]),installed_sample=sha(converted[name])) for name in NAMES}}
    try:
        for name,data in converted.items():(folder/name).write_bytes(data)
        with Session() as s:
            s.load('test8')
            s.capture('qwen-map-base')
            for index,(x,y) in enumerate(((570,270),(450,190),(760,224))):
                s.message(0x200,x,y);time.sleep(.5)
                s.capture('qwen-region-'+str(index))
                report.setdefault('regions',[]).append(dict(mouse=[x,y],index=s.i(0x659408+0x54)))
            report['run']=str(s.run)
    finally:
        for name,data in originals.items():(folder/name).write_bytes(data)
        report['restored']=all((folder/name).read_bytes()==data for name,data in originals.items())
        path=ROOT/'modernization/logs/wide169'/('hd-realm-integration-'+str(time.time_ns())+'.json')
        path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(path,flush=True)
        if not report['restored']:raise RuntimeError('Realm sample restoration failed')


if __name__=='__main__':main()
