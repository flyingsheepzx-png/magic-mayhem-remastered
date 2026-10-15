"""User-authorized bounded save1 reproduction in isolated before/after copies."""
import argparse,os,json,shutil,time
from pathlib import Path
import numpy as np
from PIL import Image
import compare_remastered_ui_11 as c
import build_11_portable_render as p
import build_11_surface_lifecycle as lifecycle
from install_11_minimap_v2 import resources
OUT=c.ROOT/'modernization/logs/remastered-ui/portable-save1'
FIXTURE=lifecycle.DEST/'runtime/Save/1.sav'
def staged(name,wrapper):
    dest=c.ROOT/'modernization/playtests'/('portable-save1-'+name);dest.mkdir(exist_ok=False)
    rt=dest/'runtime';rt.mkdir()
    source=lifecycle.DEST/'runtime'
    # Diagnostic launcher retains flags, unlike player launcher, but embeds
    # exactly the same tested gameplay modules and FMV behavior.
    entry=dest/'MagicMayhem-Remastered-1.1.exe'
    shutil.copy2(lifecycle.OUT/'candidate.exe',entry)
    assert resources(entry)==resources(lifecycle.DEST/lifecycle.ENTRY)
    for f in c.files(source):
        rel=f.relative_to(source);n=rel.as_posix()
        if rel.parts[0].lower() in ('save','ss','logs') or n.startswith('modernization/logs/'):continue
        target=rt/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if c.mutable_name(n):shutil.copy2(f,target)
        else:os.link(f,target)
    (rt/'Save').mkdir();shutil.copy2(FIXTURE,rt/'Save'/FIXTURE.name)
    shutil.copy2(wrapper,rt/'ddraw.dll')
    identity=dict(version='1.1',launcher_name=entry.name,launcher_sha256=c.sha(entry),engine_sha256=c.ENGINES['1.1'])
    return rt,identity
def block_fraction(path):
    a=np.asarray(Image.open(path).convert('RGB'));assert a.shape==(1440,2560,3)
    return float(np.mean(np.all(a[::2,::2]==a[::2,1::2],axis=2)&np.all(a[::2,::2]==a[1::2,::2],axis=2)&np.all(a[::2,::2]==a[1::2,1::2],axis=2)))
def run(mode):
    OUT.mkdir(parents=True,exist_ok=True)
    wrapper=lifecycle.DEST/'runtime/ddraw.dll' if mode=='before' else p.OUT/'wrapper/bin/Release/ddraw.dll'
    rt,identity=staged(mode,wrapper);Base=c.session_class();s=Base(identity,rt,OUT/mode,65)
    with s:
        s.shot('menu');s.load_fixture('1');s.shot('battle')
        controls=s.controls();v={x['vtable'] for x in controls}
        assert {'0x5c6ee8','0x5c6f54'}.issubset(v),'Not battle'
        s.result['battle_profile']=dict(control_count=len(controls),unit_count=s.i(0x6def5c),world=s.i(0x6a46bc))
        # Pause before checking presentation-input inverse; no game memory writes.
        s.key(0x20);time.sleep(.2)
        s.message(0x200,2000,1000);time.sleep(.15)
        s.shot('battle-cursor',False)
        image=np.asarray(Image.open(s.records['battle-cursor']['output']).convert('RGB')).astype(int)
        crop=image[1000:1060,2000:2060];cyan=(crop[:,:,1]>crop[:,:,0]+20)&(crop[:,:,2]>crop[:,:,0]+20)&(crop[:,:,1]>130)
        s.result['cursor_at_requested_output_point']=int(cyan.sum())
        if mode!='before':assert s.result['cursor_at_requested_output_point']>=12,'Cursor inverse/output position mismatch'
        s.result['two_by_two_equal_fraction']=block_fraction(s.records['battle']['output'])
        if mode=='after':
            assert s.result['two_by_two_equal_fraction']>.999,'Battle not presented at exact2x'
            # Save1 tutorial consumes Escape: retain observations, do not
            # claim the independent page transition was exercised here.
            s.key(0x1b);time.sleep(.6);s.shot('escape')
            s.key(0x1b);time.sleep(.6);s.shot('battle-return')
            assert block_fraction(s.records['battle-return']['output'])>.999
    assert s.result['restored'] and not s.result['cleanup_errors']
    if mode in ('after','input'):
        before=json.loads((OUT/'before/capture.json').read_text(encoding='utf-8'))
        assert before['two_by_two_equal_fraction']<.98,'Before did not reproduce'
        assert before['fixture_sha256']==s.result['fixture_sha256']==c.sha(FIXTURE)
        v=json.loads((p.OUT/'verification.json').read_text());v['save1_comparison']=dict(result='passed',fixture_sha256=c.sha(FIXTURE),before_fraction=before['two_by_two_equal_fraction'],after_fraction=s.result['two_by_two_equal_fraction'],cursor_at_requested_output_point=s.result['cursor_at_requested_output_point'],menu_fonts=s.records['menu']['font_heights'],battle_fonts=s.records['battle']['font_heights'],logs=str(OUT),limitation='Tutorial intercepts Escape; independent menu transitions not exercised',runtime_acceptance='isolated comparison passed; installed user acceptance pending')
        p.write(p.OUT/'verification.json',v)
    print(mode,'save1 capture completed',s.result['two_by_two_equal_fraction'],s.result['cursor_at_requested_output_point'])
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('mode',choices=['before','after','input']);run(a.parse_args().mode)
