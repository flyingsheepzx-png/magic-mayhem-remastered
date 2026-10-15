"""Read-only ANI structural checks and real native first-event stepping."""
import hashlib,json,struct
from pathlib import Path
from verify_ai_training_math import machine,put
from verify_ai_action_primitives import call
from verify_ai_groups import word
from verify_ai_model_native import ROOT,SHA

RUNTIME=Path('D:/Games/Magic&Mayham_Remastered_1.1/runtime')

def inspect(path):
    data=path.read_bytes();assert data[:4]==b'ANI\0'
    size,records_count,version,reserved,index_count=struct.unpack_from('<5I',data,4)
    assert size==len(data) and version==5
    start=44+index_count*4;assert start+records_count*44==len(data)
    indices=struct.unpack_from('<'+'I'*index_count,data,44)
    assert indices[0]==0 and indices[-1]==records_count and list(indices)==sorted(indices)
    ops=[struct.unpack_from('<I',data,start+i*44)[0] for i in range(records_count)]
    assert set(ops)<=set(range(7))
    u=machine();obj=0x2010000;bank=obj+0x1000;index_base=bank+0x200;record_base=bank+0x2000
    put(u,bank+4,'II',index_base,record_base);put(u,index_base,'I'*index_count,*indices)
    u.mem_write(record_base,data[start:]);rows=[]
    for animation in range(index_count-1):
        call(u,0x464c50,obj,[]);call(u,0x464ca0,obj,[bank]);call(u,0x464cb0,obj,[animation,0])
        seen=set();steps=0;event=0;status='pending'
        if not word(u,obj+8):status='ended_during_initialization'
        else:
            for tick in range(10000):
                state=bytes(u.mem_read(obj,48))
                if state in seen:status='zero_event_cycle';break
                seen.add(state);event=call(u,0x464ec0,obj,[]);steps+=1
                if event:status='first_nonzero_event';break
            else:status='step_budget'
        assert status!='pending'
        rows.append(dict(animation_index=animation,record_begin=indices[animation],record_end=indices[animation+1],status=status,steps=steps,event=event))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==hashlib.sha256(data).hexdigest()
    return dict(path=str(path),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),version=version,reserved=reserved,record_count=records_count,index_count=index_count,sprite_name=data[24:44].split(b'\0')[0].decode('ascii'),opcode_counts={str(op):ops.count(op) for op in range(7)},animations=rows)

def verify():
    paths=sorted(p for p in (RUNTIME/'Sprites').glob('*') if p.suffix.lower()=='.ani' and p.stem.lower().startswith('effects'))
    assert len(paths)==13
    assets=[inspect(p) for p in paths]
    report=dict(result='passed',engine_sha256=SHA,assets=assets,scope='Read-only13 installed Effects ANI files; empirical version5 header/index/44-byte records structurally checked and raw records staged into native VM. Real464c50/464ca0/464cb0/465000/464ec0,no doubles. First-event/zero-event-cycle classification; parser mapping not yet confirmed against native disk loader,animation IDs not yet linked to spell directory. Sources hash checked before/after; no player process or file mutation.')
    (ROOT/'modernization/docs/ai-animation-assets-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    statuses={}
    for asset in assets:
        for row in asset['animations']:statuses[row['status']]=statuses.get(row['status'],0)+1
    print(dict(result='passed',files=len(assets),animations=sum(len(a['animations']) for a in assets),statuses=statuses))

if __name__=='__main__':verify()
