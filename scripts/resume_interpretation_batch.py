#!/usr/bin/env python3
"""Resume independent fictional evaluation trials without repeating completed requests."""
import argparse,concurrent.futures,datetime,json,pathlib,subprocess,sys,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('report',type=pathlib.Path);p.add_argument('--fixtures',type=pathlib.Path,default=root/'tests/fixtures/architecture-scenarios.json');p.add_argument('--trials',type=int,default=3);p.add_argument('--jobs',type=int,choices=[1,2,3,4],default=3);p.add_argument('--env-file',default='.env');p.add_argument('--secret-env',default='DEEPSEEK_API_KEY');a=p.parse_args()
report=json.loads(a.report.read_text());cases=json.loads(a.fixtures.read_text());parts=root/'implementation/copilot/batch-parts'/a.report.stem;parts.mkdir(parents=True,exist_ok=True)
for name,expected in report['versions'].items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:raise SystemExit('Implementation changed. Start a new evaluation rather than mixing versions.')
tasks=[]
for c in cases:
 done=[t for t in report['trials'] if t['scenario']==c['id']]
 if len(done)<a.trials:tasks.append((c['id'],len(done),a.trials-len(done)))
def run(task):
 sid,offset,count=task;output=parts/(sid+'.json');argv=[sys.executable,str(root/'scripts/evaluate_copilot_live.py'),'--provider',report['provider'],'--model',report['model'],'--reasoning',report.get('reasoning_effort','disabled'),'--secret-env',a.secret_env,'--env-file',a.env_file,'--fixtures',str(a.fixtures),'--trials',str(count),'--scenario',sid,'--output',str(output)]
 proc=subprocess.run(argv,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if not output.exists():return sid,[],{'error':'No result artifact','exit_code':proc.returncode}
 part=json.loads(output.read_text());rows=part['trials']
 for row in rows:row['trial']+=offset;row['batch_evidence']=str(output.relative_to(root))
 return sid,rows,part.get('execution_error')
print('Remaining scenario batches:',len(tasks),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:
 for future in concurrent.futures.as_completed([pool.submit(run,t) for t in tasks]):
  sid,rows,error=future.result();report['trials'].extend(rows);report['trials'].sort(key=lambda t:(t['scenario'],t['trial']));report['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  if error:report.setdefault('batch_errors',[]).append({'scenario':sid,'error':error})
  a.report.write_text(json.dumps(report,indent=2)+'\n');print(sid,len(rows),'recorded',flush=True)
report['evaluation_complete']=len(report['trials'])==len(cases)*a.trials
report['release_approved']=False;a.report.write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if report['evaluation_complete'] else 1)
