from pathlib import Path
import json,time,hashlib
import run_trials as t
root=t.ROOT
jobs=[]
for name in ['01-full-conservative','02-full-readable','03-context-crop','03-context-crop-v2']:
 record=t.load_json(name+'-call.json'); job_id=record['manager_job_id']
 try:
  job=t.api('/api/keyframe2/jobs/'+job_id)['job']
  terminal=job.get('status')
  entry={'candidate':name,'manager_job_id':job_id,'status':terminal,'phase':job.get('phase_code') or job.get('phase'),'engine':job.get('engine'),'queried_local':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'source':'read-only Manager job query','actual_output_retained':(root/(name+'-raw.png')).is_file()}
  record['terminal_status']=terminal
  record['closeout_service_status']=entry
  t.write_json(name+'-call.json',record)
 except Exception as exc:
  entry={'candidate':name,'manager_job_id':job_id,'last_recorded_status':record.get('terminal_status'),'query_error_type':type(exc).__name__,'source':'existing recorded terminal state; live query unavailable','actual_output_retained':(root/(name+'-raw.png')).is_file()}
 jobs.append(entry)
before=t.load_json('03-context-crop-v2-preflight.json'); current=t.verify()
t.write_json('closeout.json',{'date':'2026-09-30','decision':'User reviewed: none of three completed actual Qwen trials yields a directly installable balance of fidelity and readability. Prompt-led full-image/crop redraw is insufficient. Future work needs actual structural constraints and regional material processing.','generation_complete':True,'no_further_generation_authorized_in_this_closeout':True,'jobs':jobs,'source_unchanged':current['source_sha256']==before['source_sha256'],'old_output_unchanged':current['old_sha256']==before['old_sha256'],'queue_bytes_unchanged':current['queue_sha256']==before['queue_sha256'],'game_run':False,'runtime_or_candidate_modified':False,'all_outputs_retained':True})
print(json.dumps(jobs,ensure_ascii=False,indent=2))
