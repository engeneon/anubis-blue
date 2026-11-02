#!/usr/bin/env python3
"""Bounded live-provider scenario evaluation on an isolated Anubis database. Never prints secrets."""
import argparse,json,os,pathlib,secrets,socket,subprocess,tempfile,time,urllib.request,urllib.error,hashlib,datetime
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--provider',choices=['openai','anthropic','deepseek','xai'],required=True);p.add_argument('--model',required=True);p.add_argument('--secret-env',required=True);p.add_argument('--env-file',type=pathlib.Path);p.add_argument('--trials',type=int,default=3);p.add_argument('--reasoning',choices=['disabled','low','high'],default='disabled');p.add_argument('--multiturn',action='store_true');p.add_argument('--scenario');p.add_argument('--fixtures',type=pathlib.Path,default=root/'tests/fixtures/architecture-scenarios.json');p.add_argument('--output',default='implementation/copilot/live-evaluation.json');args=p.parse_args()
if not 1<=args.trials<=3:raise SystemExit('Trials must be 1 to 3')
key=os.environ.get(args.secret_env)
if not key and args.env_file:
 for line in args.env_file.read_text().splitlines():
  line=line.strip()
  if line.startswith('export '):line=line[7:]
  if '=' in line and not line.startswith('#'):
   name,value=line.split('=',1)
   if name.strip()==args.secret_env:key=value.strip().strip('"').strip("'")
if not key:raise SystemExit('Named backend credential is unavailable. No request sent.')
origins={'openai':'https://api.openai.com','anthropic':'https://api.anthropic.com','deepseek':'https://api.deepseek.com','xai':'https://api.x.ai'}
paths={'openai':'/v1/chat/completions','anthropic':'/v1/messages','deepseek':'/chat/completions','xai':'/v1/chat/completions'}
cases=json.loads(args.fixtures.read_text());cases=[c for c in cases if not args.scenario or c['id']==args.scenario]
if not cases:raise SystemExit('No matching scenario')
report={'provider':args.provider,'model':args.model,'reasoning_effort':args.reasoning,'mode':'live fictional scenario interpretation','release_approved':False,'trials':[],'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'versions':{str(f):hashlib.sha256((root/f).read_bytes()).hexdigest() for f in ['src/application/copilot/facts.hpp','knowledge/workload-interpretation.json','src/adapters/model_transport.cpp','build/anubis']}}
with tempfile.TemporaryDirectory(prefix='anubis-live-eval-') as tmp:
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 token=secrets.token_urlsafe(32);env={**os.environ,'ANUBIS_TOKEN':token,'ANUBIS_AI_KEY_LIVE_EVALUATION':key};env.pop('ANUBIS_IDENTITIES',None)
 process=subprocess.Popen([str(root/'build/anubis'),'--root',str(root),'--db',tmp+'/eval.sqlite','--port',str(port)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 def api(path,body=None):
  request=urllib.request.Request(f'http://127.0.0.1:{port}/api/v1/'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(request,timeout=70) as r:return json.load(r)
  except urllib.error.HTTPError as e:
   data=json.loads(e.read());raise RuntimeError(data.get('error',{}).get('code','request_failed'))
 def wait(job):
  for _ in range(180):
   r=api('jobs/'+job['id'])
   if r['data']['state'] not in ['queued','running']:return r
   time.sleep(.5)
  raise RuntimeError('job_timeout')
 try:
  for _ in range(100):
   try:api('me');break
   except Exception:time.sleep(.1)
  profile=api('copilot-profiles',dict(name='Live evaluation',provider=args.provider,origin=origins[args.provider],path=paths[args.provider],model=args.model,secret_env='ANUBIS_AI_KEY_LIVE_EVALUATION',enabled=True,max_turns=3,max_output_tokens=8192,data_policy='public',**({'reasoning_effort':args.reasoning} if args.provider=='deepseek' else {})))
  health=wait(api('copilot-profiles/'+profile['id']+'/test',{}));report['capability']=health['data']
  if health['data']['state']!='succeeded':raise RuntimeError('capability_failed')
  for case in cases:
   for trial in range(args.trials):
    c=api('cases',{'name':case['name']});s=api('copilot-sessions',{'case_id':c['id'],'classification':'public'});api('copilot-sessions/'+s['id']+'/sources',{'name':case['id']+' fictional story','kind':'message','text':case['story']})
    job=wait(api('copilot-sessions/'+s['id']+'/turns',{'profile_id':profile['id']}));row={'scenario':case['id'],'trial':trial+1,'state':job['data']['state'],'expected_patterns':case['expected_patterns'],'review_criterion':case['acceptance'],'usage':job['data'].get('usage',{}),'correction_attempts':job['data'].get('correction_attempts',[])}
    if 'proposal_id' in job['data']:
     proposal=api('copilot-proposals/'+job['data']['proposal_id']);row['proposal']=proposal['data'];row['suggested_patterns']=[x.get('pattern') for x in proposal['data']['preview'].get('components',[])];row['needs_human_review']=True
    else:row['error']=job['data'].get('error',{})
    if args.multiturn and 'proposal' in row:
     prop=row['proposal'];selected=list(range(len(prop['changes'])))
     if selected:
      accepted=api('copilot-proposals/'+proposal['id']+'/apply',{'selected':selected,'accept_assumptions':True})
      components=accepted['session']['data']['input']['components']
      activity=components[0]['name'] if components else 'Service'
      answer=f'For activity {activity}, explicitly assume the model preset dense8b with 2000 input tokens and 500 output tokens per model call. Preserve all previously accepted architecture, placement and traffic facts.'
      api('copilot-sessions/'+s['id']+'/sources',{'name':'Fictional consultant clarification','kind':'message','text':answer})
      follow=wait(api('copilot-sessions/'+s['id']+'/turns',{'profile_id':profile['id']}));row['followup_state']=follow['data']['state']
      if 'proposal_id' in follow['data']:
       fp=api('copilot-proposals/'+follow['data']['proposal_id']);row['followup_proposal']=fp['data']
       selection=list(range(len(fp['data']['changes'])))
       if selection:
        accepted=api('copilot-proposals/'+fp['id']+'/apply',{'selected':selection,'accept_assumptions':True});d=accepted['draft'];row['accepted_input']=accepted['session']['data']['input']
        # Freeze requires optimistic concurrency, keeping the production API contract intact.
        req=urllib.request.Request(f'http://127.0.0.1:{port}/api/v1/drafts/'+d['id']+'/freeze',data=b'{}',headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','If-Match':str(d['version'])})
        with urllib.request.urlopen(req,timeout=10) as response:rev=json.load(response)
        compilation=wait(api('compilations',{'revision_id':rev['id']}));row['compilation_state']=compilation['data']['state']
        if 'result_id' in compilation['data']:
         result=api('copilot-facts/'+compilation['data']['result_id']);row['planning']=result['planning']
         projection=api('neon-projections',{'result_id':compilation['data']['result_id'],'mapping':{'candidate_id':'planning:factory','platform':'HGX_B300','network_fabric':'Spectrum-X'}});row['handoff_payload']=projection['data']['payload']
    report['trials'].append(row);(root/args.output).write_text(json.dumps(report,indent=2)+'\n');print(case['id'],trial+1,row['state'],flush=True)
 except Exception as e:report['execution_error']=str(e)
 finally:process.terminate();process.wait(timeout=10);(root/args.output).write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(1 if report.get('execution_error') or any(r['state']!='succeeded' for r in report['trials']) else 0)
