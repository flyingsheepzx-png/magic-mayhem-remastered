"""Compare terrain gradients in highlighted regions to the unhighlighted map."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image


def gradients(image):
    image=image.convert('L')
    p=image.load()
    return p,image.size


def score(a,b,box,dx,dy):
    ap,_=a;bp,_=b
    numerator=aa=bb=0
    for y in range(box[1]+1,box[3]-1,2):
        for x in range(box[0]+1,box[2]-1,2):
            for ax,ay in ((1,0),(0,1)):
                av=ap[x+ax,y+ay]-ap[x-ax,y-ay]
                bv=bp[x+dx+ax,y+dy+ay]-bp[x+dx-ax,y+dy-ay]
                numerator+=av*bv;aa+=av*av;bb+=bv*bv
    return numerator/math.sqrt(aa*bb) if aa and bb else 0


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('run',type=Path)
    parser.add_argument('--base',default=None,
                        help='Screenshot in run directory to compare against')
    parser.add_argument('--captures',nargs=3,default=['aligned-0','aligned-1','aligned-2'])
    args=parser.parse_args()
    backdrop=gradients(Image.open(args.run/args.base if args.base else
                                 'game-wide169/Interface/RealmViewer/800x600/Celtic_Map.bmp'))
    checks=[]
    for name,box in zip(args.captures,[(650,140,713,205),
                                      (430,35,570,85),
                                      (655,310,728,359)]):
        overlay=gradients(Image.open(args.run/(name+'.png')))
        ranked=sorted((score(backdrop,overlay,box,x,y),x,y)
                      for y in range(-12,13) for x in range(-12,13))
        best,x,y=ranked[-1]
        checks.append(dict(capture=name,landmark=box,best_shift=[x,y],
                           gradient_correlation=best,at_zero=score(backdrop,overlay,box,0,0),
                           aligned=abs(x)<=1 and abs(y)<=1 and best>.45))
    output=args.run/'texture-alignment.json'
    output.write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print(json.dumps(checks,indent=2))
    if not all(row['aligned'] for row in checks):raise SystemExit('Texture alignment gate failed')


if __name__=='__main__':main()
