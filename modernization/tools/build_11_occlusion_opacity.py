"""Small occlusion-opacity delta on latest installed 1.1; no gameplay run."""
import argparse,shutil,subprocess,json
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
OUT=b.ROOT/'modernization/build/remastered-1.1-occlusion-opacity'
BACK=b.ROOT/'modernization/backups/remastered-1.1-occlusion-opacity'
def build():
 source=b.ROOT/'modernization/build/remastered-1.1-local-route'
 current=resources(b.TARGET/'MagicMayhem-Remastered-1.1.exe')
 assert current[101]==(source/'repath.dll').read_bytes() and current[102]==(source/'qol_bindings.dll').read_bytes()
 OUT.mkdir(exist_ok=False)
 for p in source.iterdir():
  if p.suffix in ('.cpp','.h','.inc','.rc','.cmd','.ico') or p.name=='qol_bindings.dll':shutil.copy2(p,OUT/p.name)
 p=OUT/'render_replay_trial.cpp';s=p.read_text()
 old='''            target[x]=(uint16_t)(((target[x]&0xf7de)>>1)+((body[x]&0xf7de)>>1)+
                                  (target[x]&body[x]&0x0821));'''
 new='''            target[x]=occluded_blend(target[x],body[x]);'''
 s=b.replace_once(s,old,new)
 needle='static void draw_occluded_units(unsigned char* buffer,double fraction) {'
 helper='''// Covered body opacity is 3/8 (37.5%), scene is 5/8. Compute each
// RGB565 channel separately to avoid cross-channel carries and dark rounding.
static uint16_t occluded_blend(uint16_t scene,uint16_t body) {
    unsigned r=(5*((scene>>11)&31)+3*((body>>11)&31)+4)>>3;
    unsigned g=(5*((scene>>5)&63)+3*((body>>5)&63)+4)>>3;
    unsigned b=(5*(scene&31)+3*(body&31)+4)>>3;
    return (uint16_t)((r<<11)|(g<<5)|b);
}
'''
 s=b.replace_once(s,needle,helper+needle);p.write_text(s)
 subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
 for n in ['candidate.exe','release.exe']:assert resources(OUT/n)[102]==current[102]
 base.write(OUT/'before.json',[dict(entry=str(e),manifest=str(m),kind=k,entry_sha256=b.sha(e),manifest_sha256=b.sha(m)) for e,m,k in base.targets()])
 verify()
def verify():
 # Execute the established compiled native rasterizer suite with new blend.
 import install_occluded_body
 i=install_occluded_body.installer;i.BUILD=OUT
 test=(b.ROOT/'modernization/tools/verify_occluded_units.py').read_text()
 test=test.replace('from emulate_terrain_diagonal import Native','from emulate_11_render import Native')
 test=test.replace('0x780f','0x6013').replace('half blend','37.5% body blend')
 exec(compile(test,'verify_occluded_units_opacity.py','exec'),{'__name__':'__main__'})
 v=json.loads((OUT/'occlusion-verification.json').read_text())
 assert v['result']=='passed' and v['dll_sha256']==b.sha(OUT/'repath.dll')
 v.update(module_sha256=b.sha(OUT/'repath.dll'),body_opacity_before=.5,body_opacity_after=.375,runtime_acceptance='offline native rasterizer passed; installed user acceptance pending')
 base.write(OUT/'verification.json',v)
def run(action):
 if action=='build':build();return
 if action=='verify':verify();return
 v=json.loads((OUT/'verification.json').read_text());assert v['result']=='passed'
 base.OUT=OUT;base.BACK=BACK
 if action=='install':base.install('occlusion_opacity_fix')
 else:base.rollback()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','verify','install','rollback']);run(p.parse_args().action)
