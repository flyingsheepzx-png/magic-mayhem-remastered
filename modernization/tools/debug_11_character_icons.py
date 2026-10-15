"""Authorized save2 character page capture in an independent runtime."""
import argparse,time,json
import debug_11_portable_save1 as d
import compare_remastered_ui_11 as c
import build_11_surface_lifecycle as life
def run(name):
    d.FIXTURE=life.DEST/'runtime/Save/2.sav'
    rt,identity=d.staged('character-'+name,life.DEST/'runtime/ddraw.dll')
    if name.startswith('after'):
        import shutil
        source=c.ROOT/'modernization/build/remastered-1.1-character-icons/candidate.exe'
        shutil.copy2(source,rt.parent/identity['launcher_name']);identity['launcher_sha256']=c.sha(source)
    out=c.ROOT/'modernization/logs/remastered-ui'/('character-icons-'+name);out.mkdir(exist_ok=False)
    s=c.session_class()(identity,rt,out/'capture',90)
    with s:
        s.shot('menu');s.load_fixture('2');s.shot('loaded')
        toolbar=lambda x:x['vtable']=='0x5c6bd0' and x['rect'][1]<200 and x['rect'][0]>1700
        buttons=sorted(c.wait_control(s,toolbar),key=lambda x:x['rect'][0])
        r=buttons[-3]['rect']
        for event in (0x200,0x201,0x202):s.message(event,(r[0]+r[2])//2,(r[1]+r[3])//2);time.sleep(.09)
        time.sleep(.8);s.shot('character')
        c.write_json(out/'controls.json',s.controls())
        s.result['spritebar_clip']={hex(a):s.i(a) for a in [0x6cbb6c,0x6e0008,0x6a49b8,0x656618]}
    print(out)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');run(p.parse_args().name)
