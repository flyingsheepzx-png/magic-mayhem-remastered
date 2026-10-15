"""Run existing regression fixtures against iteration1's rebuilt module."""
import os,json,subprocess,sys
import build_11_movement_timing as b
if os.environ.get('MM_MOVEMENT_VERIFY_MOMENTUM'):
 import build_11_movement_momentum as b
if len(sys.argv)>1:
 name=sys.argv[1];p=b.b.ROOT/'modernization/tools'/name;s=p.read_text(encoding='utf-8')
 if name=='verify_11_roof_ghost.py':
  os.environ['MM_ROOF_VERIFY_V2']='1'
  s=s.replace('import build_11_roof_ghost as b','import build_11_movement_timing as b').replace('import build_11_roof_ghost_v2 as b','import build_11_movement_timing as b')
 elif name=='verify_11_dynamic_wait.py':s=s.replace('import build_11_dynamic_wait as b','import build_11_movement_timing as b')
 else:
  s=s.replace('remastered-1.1-wrap-route-v1','remastered-1.1-movement-timing').replace('remastered-1.1-command-response-v2','remastered-1.1-movement-timing')
 if os.environ.get('MM_MOVEMENT_VERIFY_MOMENTUM'):
  s=s.replace('import build_11_movement_timing as b','import build_11_movement_momentum as b').replace('remastered-1.1-movement-timing','remastered-1.1-movement-momentum')
 exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
else:
 report=json.loads((b.OUT/'verification.json').read_text());rows=[]
 try:
  for name,result in [('verify_11_roof_ghost.py','ghost-verification.json'),('verify_11_wrap_route.py','wrap-verification.json'),('verify_11_command_response.py','command-verification.json'),('verify_11_dynamic_wait.py','verification.json')]:
   subprocess.run([sys.executable,__file__,name],check=True)
   data=json.loads((b.OUT/result).read_text());assert data['result']=='passed'
   rows.append(dict(fixture=name,checks=data['checks']))
 finally:
  # Dynamic wait's legacy report name overlaps the iteration's authoritative one.
  b.base.write(b.OUT/'verification.json',report)
 report['regressions']=rows;b.base.write(b.OUT/'verification.json',report)
 print(json.dumps(rows,indent=2))
