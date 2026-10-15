"""Decode optional AI telemetry; raw numeric IDs are never guessed into names."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

NAMES={1:'scheduler_begin',2:'scheduler_end',3:'model_input',4:'model_output',
       5:'candidate_result',6:'candidate_repeat_result',7:'candidate_eligible',
       8:'candidate_reevaluate',9:'budget_yield',10:'action_commit',
       11:'execution_return',12:'retirement_check'}
FIELDS='kind seq tick side phase scheduler group action id vtable subject old_action old_id budget result score other_score source count elapsed_us'.split()
ENGINE='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'

def as_float(bits):
    return struct.unpack('<f',struct.pack('<I',bits))[0]

def decode(path):
    raw=path.read_bytes()
    if len(raw)<80:raise ValueError('incomplete header')
    magic,version,size,digest=struct.unpack_from('<8sII64s',raw)
    if magic!=b'MM_AI11\0' or version!=1 or size!=400 or digest.decode()!=ENGINE:
        raise ValueError('unknown AI telemetry identity/schema')
    complete=(len(raw)-80)//size
    for i in range(complete):
        words=struct.unpack_from('<100I',raw,80+i*size)
        e=dict(zip(FIELDS,words[:20]));e['event']=NAMES.get(e['kind'],'unknown')
        if e['count']>80:raise ValueError('invalid vector length')
        e['data_bits']=list(words[20:20+e['count']])
        if e['kind']==3:
            e['features_i32']=[v if v<0x80000000 else v-0x100000000 for v in e['data_bits']]
        if e['kind']==4:e['probabilities']=[as_float(v) for v in e['data_bits']]
        if e['kind'] in {5,6,7,8,10,11,12}:e['score_f32']=as_float(e['score'])
        if e['kind'] in {7,8}:e['best_score_f32']=as_float(e['other_score'])
        e['budget_i32']=e['budget'] if e['budget']<0x80000000 else e['budget']-0x100000000
        yield e

def summarize(events):
    counts=Counter();actions=Counter();latencies=[];commits=[];yields=Counter()
    for e in events:
        counts[e['event']]+=1
        if e['kind']==2:latencies.append(e['elapsed_us'])
        if e['kind']==9:yields[e['scheduler']]+=1
        if e['kind']==10:
            actions[e['id']]+=1
            commits.append({k:e[k] for k in ['seq','tick','group','id','old_id','subject','score_f32']})
    latencies.sort()
    return {'events':dict(counts),'committed_action_ids':dict(actions),
            'budget_yields_by_context':{hex(k):v for k,v in yields.items()},
            'scheduler_duration_us':{'samples':len(latencies),
                'median':latencies[len(latencies)//2] if latencies else None,
                'p95':latencies[min(len(latencies)-1,int(len(latencies)*.95))] if latencies else None,
                'max':max(latencies,default=None)},'recent_commits':commits[-20:],
            'caveat':'Durations include diagnostic overhead. Evaluator return 0 can mean pending; execution return 0 sets native flag +0x14 and is not proven a cast failure. Eligible does not mean selected. ID names/targets remain partially recovered.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trace',type=Path)
    p.add_argument('--jsonl',type=Path);a=p.parse_args()
    events=list(decode(a.trace));summary=summarize(events)
    summary['trailing_bytes']=(a.trace.stat().st_size-80)%400
    summary['snapshot_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest()
        for f in a.trace.parent.iterdir() if f.is_file() and f.name!='trace.bin' and f.suffix.lower() in {'.dat','.cfg'}}
    if a.jsonl:
        with a.jsonl.open('w',encoding='utf-8') as f:
            for e in events:f.write(json.dumps(e,ensure_ascii=False)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
