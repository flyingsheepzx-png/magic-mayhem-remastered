"""Bounded native-surface ground-target probe on the preserved test2 fixture."""
import json
import time

from wide169_trial import Session


def main():
    with Session() as s:
        s.load('test2')
        base=s.i(0x6def58)
        if [s.i(base+o) for o in (8,12,16)] != [66,48,6]:
            raise RuntimeError('Wrong test2 fixture')
        s.click(1218,650)
        if s.i(0x6e984c)!=1:
            raise RuntimeError('Wizard selection not confirmed')
        rows=[]
        for index,(x,y) in enumerate(((700,400),(760,420),(800,450),(830,430),(780,500))):
            s.message(0x200,x,y)
            time.sleep(.18)
            hover=[s.i(a) for a in (0x6c5488,0x6c5484,0x6cbb64)]
            s.click(x,y,True)
            goal=[s.i(base+o) for o in (0x96b,0x96f,0x973)]
            time.sleep(6)
            position=[s.i(base+o) for o in (8,12,16)]
            name=f'ground-{index}'
            s.capture(name)
            rows.append(dict(mouse=[x,y],hover=hover,goal=goal,position=position,
                             screenshot=str(s.run/(name+'.png'))))
            print(rows[-1],flush=True)
        (s.run/'ground-targets.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')


if __name__=='__main__':main()
