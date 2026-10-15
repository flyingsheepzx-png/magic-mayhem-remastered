"""Read native picked-object IDs for world and portrait targets."""
import os,time,json
from wide169_trial import Session
from verify_hd60_runtime import read
os.environ['MM_ALLOW_NATIVE_CLIENT']='1';os.environ['MM_ALLOW_SCALED_CLIENT']='1'
with Session() as s:
    s.load('test7');s.key(0x5a);s.key(ord('Q'))
    wizard=s.i(0x6def58)
    rows=[]
    for x,y in ((640,330),(1215,650),(640,330)):
        s.message(0x200,x,y);time.sleep(.2)
        rows.append(dict(x=x,y=y,object_id=s.i(0x644520),picked=hex(s.i(0x656600)),
            wizard=hex(wizard),wizard_id=s.i(wizard),hover_grid=[s.i(a) for a in (0x6c5488,0x6c5484,0x6cbb64)]))
    s.result['target_ids']=rows
    print(json.dumps(rows))
