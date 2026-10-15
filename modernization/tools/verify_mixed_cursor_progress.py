"""Paired page and input regression after isolated cursor/progress repair."""
import json
import time
from PIL import Image
from compare_hd_baseline import CaptureSession, ROOT


def main():
    out=ROOT/'modernization/assets/hd/cursor-progress-verification'/str(time.time_ns())
    out.mkdir(parents=True);result={}
    for label in ('hd',):
        with CaptureSession(label,out,'mixed-ui-v4',launcher_sets_mixed=True) as s:
            time.sleep(18 if label=='baseline' else 1)
            s.load_fixture('test3',False);s.shot('battle')
            s.key(0x1b);time.sleep(.4);s.shot('escape')
            for n,(x,y) in enumerate(((500,350),(1700,350),(1700,1050),(2500,700))):
                s.message(0x200,x if s.hd else x//2,y if s.hd else y//2)
                s.shot('cursor-'+str(n),False)
                with Image.open(s.records['cursor-'+str(n)]['output']) as im:
                    pixels=im.convert('RGB').crop((x,y,min(x+60,2560),min(y+60,1440))).get_flattened_data()
                    cyan=sum(g>r+20 and b>r+20 and g>130 for r,g,b in pixels)
                if cyan<12:raise RuntimeError('Cursor absent at '+str((x,y)))
                s.result['checks']['cursor-'+str(n)]=cyan
            s.click_base(640,300);time.sleep(.5);s.shot('save-page')
            if s.hd and s.records['save-page']['font_heights']!=[64,44,30]:raise RuntimeError('Independent fonts shrunk')
            s.key(0x1b);time.sleep(.4);s.shot('return')
            if s.records['return']['font_heights']!=[32,22,15]:raise RuntimeError('Battle fonts changed')
            result[label]={'records':s.records,'checks':s.result['checks'],'fixture_sha256':s.result['fixture_sha256']}
        result[label]['restored']=s.result['restored']
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(out,flush=True)


if __name__=='__main__':main()
