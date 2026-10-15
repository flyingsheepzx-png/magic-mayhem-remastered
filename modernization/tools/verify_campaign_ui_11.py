"""Verify recorded test16 layout pairs and protected runtime state; no game launch."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
import build_remastered_11 as b

ROOT=b.ROOT/'modernization/logs/remastered-ui'

def main():
 baseline=json.loads((ROOT/'test16-ui-baseline-pair-20261001/probe.json').read_text())
 candidate=json.loads((ROOT/'test16-ui-campaign-final-20261001/probe.json').read_text())
 assert baseline['fixture_sha256']==candidate['fixture_sha256']=='10048ef90dd4bee66a5bd688aa0015883c84eacc5430b1e5a6aa96d0e6bd1399'
 for record in [baseline,candidate]:
  result=record['result'];assert result['restored'] and not result['cleanup_errors'] and not result['timed_out']
 pairs=[]
 for tag in ['loaded-test16','realm-escape','character']:
  old=baseline['screens'][tag];new=candidate['screens'][tag]
  assert old['font_heights']==[32,22,15] and new['font_heights']==[64,44,30]
  if tag=='character':select=lambda x:x['vtable']=='0x5c6bd0' and x['rect'][0] in [952,1060] and x['rect'][1] in [270,330,390,450,510,570]
  elif tag=='realm-escape':select=lambda x:x['vtable']=='0x5c6c6c' and x['rect'][0]>=400 and x['rect'][1]>=200
  else:select=lambda x:x['vtable']=='0x5c6c6c' and x['rect'][3]>600
  original=[x['rect'] for x in old['controls'] if select(x)]
  actual=[x['rect'] for x in new['controls']]
  assert original
  for rect in original:assert [v*2 for v in rect] in actual,(tag,rect)
  pairs.append(dict(page=tag,control_rectangles=len(original),scale=2))
  image=Image.open(new['output']);assert image.size==(2560,1440)
  if tag!='realm-escape':
   rgb=np.array(image.convert('RGB'))
   # Captures deliberately park the software cursor at (20,1400) in the margin.
   assert not rgb[:1350,:320].any() and not rgb[:1350,2240:].any()
 assert len([x for x in candidate['screens']['character-clear']['controls'] if x['vtable']=='0x5c6bd0' and x['rect'][0]>1800 and x['rect'][1]>400])==12
 assert all(name in candidate['screens'] for name in ['character-plus','character-minus'])
 states=[Image.open(candidate['screens'][name]['output']).convert('RGB') for name in ['character-clear','character-plus','character-minus']]
 before,plus,minus=[np.array(im) for im in states]
 changed=np.any(before!=plus,axis=2);assert int(changed.sum())>100
 # Cursor/hover transitions also change pixels. Measure the actual mana+XP fields.
 field=(slice(290,414),slice(1880,2216))
 xp_changed=int(np.any(before[field]!=plus[field],axis=2).sum());assert xp_changed>20
 xp_restored=bool(np.array_equal(before[field],minus[field]));assert xp_restored
 b.verify()
 result=dict(status='passed',fixture_sha256=candidate['fixture_sha256'],pairs=pairs,character_plus_changed_pixels=int(changed.sum()),experience_field_changed_pixels=xp_changed,minus_restores_experience_field=xp_restored,mutable_state_restored=True,protected_baselines_unchanged=True,limits='Scoped test16 pages; no battle regression, other campaign pages, region highlight or Portmanteau drag acceptance implied.')
 b.write(ROOT/'test16-ui-campaign-final-20261001/verification.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
