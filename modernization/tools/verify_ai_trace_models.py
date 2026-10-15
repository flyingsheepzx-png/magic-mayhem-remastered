"""Cross-check live diagnostic model pairs against immutable session Brain."""
import argparse,hashlib,json
from pathlib import Path
from read_ai_diagnostics_11 import decode
from ai_model_codec import read_models,score
from verify_ai_model_native import NativeScore,ROOT,SHA

def verify(trace):
    brain=next(p for p in trace.parent.iterdir() if p.name.lower()=='brain.dat')
    models={m['action_id']:m for m in read_models(brain)['models']}
    native=NativeScore(ROOT/'modernization/playtests/remastered-1.1-p1/runtime/Chaos-Wide169-engine.exe')
    pending=[];cases=[]
    for e in decode(trace):
        if e['kind']==3:pending.append(e)
        elif e['kind']==4:
            assert pending,'unpaired model output'
            before=pending.pop();assert before['id']==e['id'] and before['action']==e['action']
            expected=score(models[e['id']],before['features_i32'],**native.constants)
            error=max(abs(x-y) for x,y in zip(expected,e['probabilities']))
            assert error<0.00003,(before['seq'],error)
            cases.append(dict(seq=before['seq'],action_id=e['id'],dimension=before['count'],error=error))
    assert cases and not pending
    return dict(result='passed',engine_sha256=SHA,brain_sha256=hashlib.sha256(brain.read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),cases=len(cases),max_probability_error=max(c['error'] for c in cases),per_case=cases,scope='Recorded live model inputs/outputs versus recovered formula using pre-start session Brain; does not validate all target/learning behavior')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();r=verify(a.trace)
    if a.output:a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print({k:v for k,v in r.items() if k!='per_case'})
