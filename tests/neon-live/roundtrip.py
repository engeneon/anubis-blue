#!/usr/bin/env python3
"""Real local binary-to-binary integration, isolated from all saved customer projects."""
import argparse,hashlib,json,os,pathlib,socket,subprocess,tempfile,time,urllib.request,urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--neon-root',type=pathlib.Path,required=True);a=p.parse_args()
def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def request(base,path,body=None,method=None,headers=None):
 req=urllib.request.Request(base+'/api/v1/'+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json',**(headers or {})},method=method)
 try:
  with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
 except urllib.error.HTTPError as e:
  with e:raise RuntimeError(str(e.code)+': '+e.read().decode()[:1000])
report={'scope':'isolated-local-stateless-roundtrip','production_qualified':False}
with tempfile.TemporaryDirectory() as temp:
 t=pathlib.Path(temp);np,ap=port(),port();nb,ab=f'http://127.0.0.1:{np}',f'http://127.0.0.1:{ap}'
 target={'id':'neon-local-probe','base_url':nb,'api_version':'1.1.0','mode':'stateless_local_experimental','contract_evidence_sha256':hashlib.sha256((ROOT/'implementation/release-evidence/neon-local-probe.json').read_bytes()).hexdigest()}
 (t/'target.json').write_text(json.dumps(target));token='isolated-roundtrip-'+('x'*32);headers={'Authorization':'Bearer '+token}
 processes=[]
 with open(t/'neon.log','w+') as nl,open(t/'anubis.log','w+') as al:
  try:
   processes.append(subprocess.Popen([str(a.neon_root/'build/aifactorycad-reference-ui-server'),str(np)],cwd=temp,env={**os.environ,'AIFACTORYCAD_RUNTIME_ROOT':str(t/'neon'),'AIFACTORYCAD_API_PROFILE':'development_unsecured','AIFACTORYCAD_SECURITY_CONFIG':str(a.neon_root/'config/local_api_security.json')},stdout=nl,stderr=nl))
   processes.append(subprocess.Popen([str(ROOT/'build/anubis'),'--root',str(ROOT),'--db',str(t/'anubis/db.sqlite'),'--port',str(ap)],env={**os.environ,'ANUBIS_TOKEN':token,'ANUBIS_NEON_TARGET':str(t/'target.json')},stdout=al,stderr=al))
   for base,h in [(nb,{}),(ab,headers)]:
    for _ in range(100):
     try:request(base,'capabilities',headers=h);break
     except Exception:time.sleep(.1)
    else:raise RuntimeError('Service startup failed')
   def api(path,body=None,method=None,extra=None):return request(ab,path,body,method,{**headers,**(extra or {})})
   case=api('cases',{'name':'Local Neon loop'});draft=api('cases/'+case['id']+'/drafts',json.loads((ROOT/'tests/fixtures/synthetic.json').read_text()))
   pack=api('packs',json.loads((ROOT/'knowledge/synthetic.json').read_text()));activation=api('packs/'+pack['id']+'/activate',{'channel':'demonstration'})
   revision=api('drafts/'+draft['id']+'/freeze',{},extra={'If-Match':'1'})
   def wait(job,key):
    for _ in range(180):
     j=api('jobs/'+job['id'])['data']
     if key in j:return j[key]
     if j['state'] in ['failed','outcome_unknown']:raise RuntimeError(str(j))
     time.sleep(.5)
    raise RuntimeError('Job timed out')
   run=api('results/'+wait(api('compilations',{'revision_id':revision['id'],'activation_id':activation['id']}),'result_id'))
   candidate=run['data']['result']['candidates'][0];assert candidate['gpus']==56
   projection=api('neon-projections',{'result_id':run['id'],'mapping':{'candidate_id':candidate['id'],'platform':'HGX_B300','network_fabric':'InfiniBand','accept_substitution':True}})
   payload={'projection_id':projection['id'],'confirm_experimental_submission':True};job=api('neon-submissions',payload,extra={'Idempotency-Key':'single-submission'})
   again=api('neon-submissions',payload,extra={'Idempotency-Key':'single-submission'});assert again['id']==job['id']
   assessment=api('assessments/'+wait(job,'assessment_id'))['data']
   assert assessment['transport']['http_status']==200
   assert assessment['external_authority']['governance']['engineering_use']=='not_engineering_approved'
   assert assessment['field_reconciliation'][0]['status']=='external_adjustment'
   assert all(x['status']=='unverifiable' for x in assessment['domains'])
   report.update(passed=True,requested_gpus=56,returned_gpus=assessment['field_reconciliation'][0]['returned'],authority_preserved=True,idempotency_passed=True,domain_verification_not_inferred=True,target_binary_sha256=hashlib.sha256((a.neon_root/'build/aifactorycad-reference-ui-server').read_bytes()).hexdigest())
  except Exception as e:
   report.update(passed=False,error=str(e));nl.flush();al.flush();nl.seek(0);al.seek(0);report['logs']={'neon':nl.read()[-2000:],'anubis':al.read()[-2000:]}
  finally:
   for proc in processes:proc.terminate()
   for proc in processes:proc.wait(timeout=10)
(ROOT/'implementation/release-evidence/neon-roundtrip.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
