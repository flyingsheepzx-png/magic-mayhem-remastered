"""Offline asset provenance and actual test17 native render comparison."""
import json
import numpy as np
from PIL import Image
import build_11_qwen_highlight as h
def main():
 v=json.loads((h.OUT/'verification.json').read_text());assert v['regions']==41
 root=h.b.ROOT/'modernization/logs/remastered-ui';before=root/'test17-highlight-before';after=root/'test17-highlight-final'
 a=json.loads((before/'probe.json').read_text());b=json.loads((after/'probe.json').read_text());assert a['fixture_sha256']==b['fixture_sha256']
 for p in [a,b]:assert p['result']['restored'] and not p['result']['cleanup_errors'] and not p['result']['timed_out']
 for world,digest in v['maps'].items():assert h.b.sha(h.RT/f'Interface/RealmViewer/800x600/{world}_Map.PNG')==digest
 for r in v['records']:assert h.b.sha(h.RT/r['path'])==r['sha256'] and h.b.sha(h.RT/r['mask_path'])==r['mask_sha256'] and r['outside_exact']
 rgb=lambda p:np.array(Image.open(p).convert('RGB')).astype(float)
 actual=rgb(after/'1.1/forest-2560x1440.png');old=rgb(before/'1.1/forest-2560x1440.png');expected=rgb(h.RT/'Interface/RealmViewer/hd-selected/Celtic_01.PNG')
 roi=(slice(960,1080),slice(1550,1700));delta=abs(actual[roi]-expected[roi]);assert delta.max()<=7
 new=rgb(after/'1.1/unhover-2560x1440.png');original=rgb(before/'1.1/unhover-2560x1440.png');assert np.array_equal(new[roi],original[roi])
 h.b.verify();report=dict(status='passed',regions=41,fixture_sha256=b['fixture_sha256'],native_rgb565_max_error=float(delta.max()),new_mae=float(delta.mean()),previous_mae=float(abs(old[roi]-expected[roi]).mean()),unhover_roi_exact=True,maps_unchanged=True,masks_unchanged=True,mutable_restored=True,limits='All41 assets validated offline; live hover on test17 Celtic Forest of Pain only; Greek/Medieval remain user acceptance')
 h.b.write(after/'verification.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
