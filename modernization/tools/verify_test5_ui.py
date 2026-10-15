"""Check complete talisman colour regions in the test5 character capture."""
from pathlib import Path
import argparse,json
from PIL import Image
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    r=json.loads(args.report.read_text())
    if r['status']!='completed' or r['changed_saves'] or not r['restored']:
        raise RuntimeError('Trial failed or changed files/saves')
    with Image.open(r['screenshots'][-1]) as im:
        im=im.convert('RGB')
        if im.size!=(1120,840): raise RuntimeError('Unexpected native surface')
        checks={}
        for name,y,c in [('law',546,2),('neutral',616,1),('chaos',686,0)]:
            crop=im.crop((377,y-22,420,y+22))
            points=[(x,yy) for yy in range(44) for x in range(43)
                    if (v:=crop.getpixel((x,yy)))[c]>60
                    and v[c]>max(v[k] for k in range(3) if k!=c)*1.4]
            if len(points)<200 or max(y for x,y in points)-min(y for x,y in points)<26:
                raise RuntimeError('Clipped or missing talisman: '+name)
            checks[name]=len(points)
    print(json.dumps({'complete_talismans':checks,'saves_unchanged':True}))
if __name__=='__main__': main()
