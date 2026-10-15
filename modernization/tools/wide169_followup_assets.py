"""Rebuild only the three misplaced generic left Grimoire pages."""
from pathlib import Path
import io
import json

from PIL import Image
from qwen_canvas import grimoire_key_template, apply_grimoire_key_template
from wide169_build import ROOT, BUILD, sha

state=json.loads((ROOT/'modernization/assets/hd/ui-fit.json').read_text())
backup=ROOT/'modernization/assets/hd/backups/ui-fit'
target=BUILD/'followup-assets'
for index,row in enumerate(state['files']):
    rel=Path(row['path'])
    if rel.name not in ('GenericL01.JPG','GenericL02.JPG','GenericL03.JPG') or 'Grimoire' not in rel.parts:
        continue
    raw=(backup/str(index)).read_bytes()
    if sha(raw)!=row['original_sha256']:
        raise RuntimeError('Unknown source '+str(rel))
    image=Image.open(io.BytesIO(raw)).convert('RGB')
    if image.size!=(400,600):
        raise RuntimeError('Unexpected source size '+str(rel))
    template=grimoire_key_template(image)
    scaled=apply_grimoire_key_template(image.resize((480,720),Image.Resampling.NEAREST),template)
    result=Image.new('RGB',(640,720),(0,0,255))
    result.paste(scaled,(160,0))
    folder=target/rel.parent
    folder.mkdir(parents=True,exist_ok=True)
    result.save(folder/rel.name,'JPEG',quality=100,subsampling=0)
    result.save(folder/rel.with_suffix('.PNG').name,'PNG',compress_level=9,optimize=True)
print(target)
