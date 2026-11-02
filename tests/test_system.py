"""Independent story arithmetic and API lifecycle regressions. No performance claims."""
import copy, json, os, pathlib, socket, subprocess, tempfile, time, unittest, urllib.request, urllib.error
from fractions import Fraction
ROOT=pathlib.Path(__file__).resolve().parents[1]
BIN=pathlib.Path(os.environ.get('ANUBIS_TEST_BINARY',str(ROOT/'build/anubis')))
def fixture(name): return json.loads((ROOT/f'tests/fixtures/{name}.json').read_text())
def compile_workload(w,pack=None):
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d)/'w.json';p.write_text(json.dumps(w))
  cmd=[str(BIN),'compile',str(p)]
  if pack:
   k=pathlib.Path(d)/'pack.json';k.write_text(json.dumps(pack));cmd.append(str(k))
  return subprocess.run(cmd,text=True,capture_output=True)
def fact(r,name,stage=None,scenario=None):
 for f in r['facts']:
  if f['name']==name and (stage is None or f['stage_id']==stage) and (scenario is None or f['scenario_id']==scenario):return Fraction(int(f['exact']['numerator']),int(f['exact']['denominator']))
 raise AssertionError(name)
class Compiler(unittest.TestCase):
 def test_meridian_partial(self):
  r=json.loads(compile_workload(fixture('meridian')).stdout)
  self.assertEqual(fact(r,'transactions_per_second','assistant'),10)
  self.assertEqual(fact(r,'model_calls_per_second','assistant'),Fraction(25,2))
  self.assertEqual(fact(r,'reports_per_second','reports'),Fraction(25,24))
  self.assertEqual(r['candidates'],[])
 def test_harbor(self):
  r=json.loads(compile_workload(fixture('harbor')).stdout)
  for scenario,calls,ins,outs in [('normal',80,160000,32000),('simultaneous',220,440000,88000),('failure',100,200000,40000)]:
   for name,target in [('model_calls_per_second',calls),('input_tokens_per_second',ins),('output_tokens_per_second',outs)]:
    total=sum(Fraction(int(f['exact']['numerator']),int(f['exact']['denominator'])) for f in r['facts'] if f['scenario_id']==scenario and f['name']==name)
    self.assertEqual(total,target)
 def test_aster(self):
  r=json.loads(compile_workload(fixture('aster')).stdout)
  self.assertEqual(fact(r,'calendar_tokens_per_second'),Fraction(120_000_000_000,30*86400))
  self.assertEqual(fact(r,'effective_tokens_per_second'),Fraction(120_000_000_000,30*86400)*Fraction(100,85))
  self.assertEqual(fact(r,'payload_rate'),Fraction(60*10**12,12*3600))
  self.assertEqual(fact(r,'durable_write_GiBps'),Fraction(2*1024,120))
  self.assertEqual(fact(r,'retained_upper_bound_bytes'),68*2**40)
  w=fixture('aster');w['stages'][2]['observations']['retention_overlap']={'state':'known','value':'4','unit':'count','origin':'customer','source':'explicit overlap'}
  r=json.loads(compile_workload(w).stdout);self.assertEqual(fact(r,'retained_bytes'),60*2**40)
 def test_replica_oracle_and_memory_failure(self):
  w=fixture('synthetic');p=json.loads((ROOT/'knowledge/synthetic.json').read_text());r=json.loads(compile_workload(w,p).stdout)
  self.assertEqual((r['candidates'][0]['gpus'],r['candidates'][0]['nodes'],r['candidates'][0]['status']),(56,7,'pass'))
  p['profiles'][0]['memory_required_bytes']='90000000000';r=json.loads(compile_workload(w,p).stdout);self.assertEqual(r['candidates'][0]['status'],'fail')
 def test_changed_prompt_cannot_reuse_stale_fingerprint(self):
  w=fixture('synthetic');p=json.loads((ROOT/'knowledge/synthetic.json').read_text());w['stages'][0]['observations']['input_tokens']['value']='10000'
  r=json.loads(compile_workload(w,p).stdout);self.assertEqual(r['candidates'][0]['status'],'fail')
 def test_product_specific_storage_evidence(self):
  known=lambda value,unit:{'state':'known','value':value,'unit':unit,'origin':'customer','source':'synthetic test'}
  w={'schema_version':'1.0','name':'Storage test','stages':[{'id':'data','type':'data','storage_tier':'object','protocols':['S3'],'resource_fingerprint':{'tier':'object','layout':'test-1'},'observations':{'bytes':known('1','TiB'),'free_fraction':known('0.2','ratio'),'read_rate':known('1','GiB/s'),'write_rate':known('0','B/s')}}],'scenarios':[{'id':'normal'}]}
  p={'schema_version':'1.0','id':'test-storage','version':'1','channel':'synthetic','profiles':[],'resource_profiles':[{'id':'storage-1','kind':'storage','vendor':'Fictional vendor','product':'Test object system','configuration':'test-1','fingerprint':{'tier':'object','layout':'test-1'},'protocols':['S3'],'usable_bytes':'2199023255552','read_Bps':'2000000000','write_Bps':'2000000000','source':'test','evidence_basis':'synthetic','scope':'fictional configuration'}]}
  r=json.loads(compile_workload(w,p).stdout);self.assertEqual(r['resource_candidates'][0]['status'],'pass')
  p['resource_profiles'][0]['read_Bps']='1000000000';r=json.loads(compile_workload(w,p).stdout);self.assertEqual(r['resource_candidates'][0]['status'],'fail')
  p['resource_profiles'][0]['read_Bps']='2000000000';del w['stages'][0]['resource_fingerprint'];r=json.loads(compile_workload(w,p).stdout);self.assertEqual(r['resource_candidates'][0]['status'],'unknown')
 def test_replay_and_units(self):
  w=fixture('aster');r1=json.loads(compile_workload(w).stdout)
  w['stages'].reverse();w['scenarios'].reverse()
  stage=next(x for x in w['stages'] if x['id']=='campaign');stage['observations']['window']['value']='2592000';stage['observations']['window']['unit']='s'
  r2=json.loads(compile_workload(w).stdout);self.assertEqual(r1,r2)
 def test_rejects_bad_inputs(self):
  for value in ['NaN','Infinity','1e20','-1','9223372036854775808']:
   w=fixture('meridian');w['stages'][0]['observations']['users']['value']=value
   self.assertNotEqual(compile_workload(w).returncode,0,value)
  w=fixture('meridian');w['edges']=[{'from':'assistant','to':'reports'},{'from':'reports','to':'assistant'}];self.assertNotEqual(compile_workload(w).returncode,0)
  w=fixture('aster');w['stages'][0]['observations']['explicit_overhead']={'state':'known','value':'100','unit':'s','origin':'customer','source':'test'};self.assertNotEqual(compile_workload(w).returncode,0)
 def test_evidence_mismatch_unknown(self):
  w=fixture('synthetic');p=json.loads((ROOT/'knowledge/synthetic.json').read_text());p['profiles'][0]['fingerprint']['precision']='fp8'
  r=json.loads(compile_workload(w,p).stdout);self.assertEqual(r['candidates'],[]);self.assertTrue(r['questions'])
 def test_reserve_and_inactive(self):
  w=fixture('aster');w['stages'][2]['observations']['recent']['active']=False
  r=json.loads(compile_workload(w).stdout);self.assertFalse(any(f['name']=='retained_upper_bound_bytes' for f in r['facts']))
 def test_budget_truncation(self):
  w=fixture('synthetic');w['candidate_limit']=0;p=json.loads((ROOT/'knowledge/synthetic.json').read_text())
  r=json.loads(compile_workload(w,p).stdout);self.assertTrue(r['search']['truncated']);self.assertEqual(r['candidates'],[])
 def test_unknown_overhead_does_not_resolve(self):
  w=fixture('aster');w['stages'][0]['observations']['effective_fraction']={'state':'unknown','reason':'measurement pending'}
  r=json.loads(compile_workload(w).stdout)
  self.assertFalse(any(f['name']=='effective_tokens_per_second' for f in r['facts']))
  self.assertTrue(any(f['name']=='calendar_tokens_per_second' for f in r['facts']))
 def test_bounded_retry_and_partial_branch(self):
  w=fixture('synthetic');o=w['stages'][0]['observations']
  for k,v,u in [('retry_probability','0.5','ratio'),('max_retries','2','count')]:o[k]={'state':'known','value':v,'unit':u,'origin':'measurement','source':'test'}
  r=json.loads(compile_workload(w).stdout);self.assertEqual(fact(r,'model_calls_per_second'),175)
  o['branch_probability']={'state':'known','value':'0.5','unit':'ratio','origin':'customer','source':'test'}
  r=json.loads(compile_workload(w).stdout);self.assertFalse(any(f['name']=='model_calls_per_second' for f in r['facts']))
 def test_joint_reservations_do_not_claim_interference_qualification(self):
  w=fixture('synthetic');p=json.loads((ROOT/'knowledge/synthetic.json').read_text())
  second=copy.deepcopy(w['stages'][0]);second['id']='second';w['stages'].append(second)
  for sc in w['scenarios']:sc['active_stages']=[x['id'] for x in w['stages']]
  r=json.loads(compile_workload(w,p).stdout)
  self.assertEqual(r['factory_configurations'][0]['gpus'],112)
 def test_duplicate_json_keys(self):
  with tempfile.NamedTemporaryFile(mode='w',suffix='.json') as f:
   f.write('{"name":"a","name":"b"}');f.flush()
   r=subprocess.run([str(BIN),'compile',f.name],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0)
class API(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.d=pathlib.Path(cls.tmp.name)
  cls.tokens={'alice':'alice_'+('x'*30),'bob':'bob_'+('x'*30),'reader':'reader_'+('x'*30),'agent':'agent_'+('x'*30)}
  ids=[dict(id=id,token=token,role='viewer' if id=='reader' else 'agent' if id=='agent' else 'admin') for id,token in cls.tokens.items()]
  (cls.d/'identities.json').write_text(json.dumps(ids))
  sock=socket.socket();sock.bind(('127.0.0.1',0));cls.port=sock.getsockname()[1];sock.close()
  cls.proc=subprocess.Popen([str(BIN),'--root',str(ROOT),'--db',str(cls.d/'test.sqlite'),'--port',str(cls.port)],env={**os.environ,'ANUBIS_IDENTITIES':str(cls.d/'identities.json')},stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  for i in range(100):
   try:urllib.request.urlopen(f'http://127.0.0.1:{cls.port}/health',timeout=1);break
   except OSError:time.sleep(.05)
  else:raise RuntimeError('Server failed: '+cls.proc.stderr.read().decode())
 @classmethod
 def tearDownClass(cls):cls.proc.terminate();cls.proc.wait(timeout=5);cls.proc.stderr.close();cls.tmp.cleanup()
 def req(self,path,method='GET',data=None,actor='alice',extra=None):
  headers={'Authorization':'Bearer '+self.tokens[actor],'Content-Type':'application/json',**(extra or {})}
  req=urllib.request.Request(f'http://127.0.0.1:{self.port}/api/v1/'+path,data=None if data is None else json.dumps(data).encode(),headers=headers,method=method)
  try:
   with urllib.request.urlopen(req,timeout=10) as r:return r.status,json.load(r)
  except urllib.error.HTTPError as e:
   with e:return e.code,json.load(e)
 def create(self,story='meridian'):
  status,c=self.req('cases','POST',{'name':'Test engagement'});self.assertEqual(status,201)
  status,d=self.req('cases/'+c['id']+'/drafts','POST',fixture(story));self.assertEqual(status,201)
  return c,d
 def test_descriptor_contract(self):
  status,d=self.req('component-descriptors');self.assertEqual(status,200,d);self.assertIn('inference',d['fields'])
 def test_access_control(self):
  c,d=self.create();self.assertEqual(self.req('drafts/'+d['id'],actor='bob')[0],403)
  self.assertEqual(self.req('cases','POST',{'name':'Forbidden'},actor='reader')[0],403)
 def test_conflict_freeze_and_replay(self):
  c,d=self.create();body=copy.deepcopy(d['data']);body['name']='Changed'
  status,updated=self.req('drafts/'+d['id'],'PATCH',body,extra={'If-Match':'1'});self.assertEqual(status,200)
  self.assertEqual(self.req('drafts/'+d['id'],'PATCH',body,extra={'If-Match':'1'})[0],409)
  status,rev=self.req('drafts/'+d['id']+'/freeze','POST',{},extra={'If-Match':str(updated['version'])});self.assertEqual(status,201)
  payload={'revision_id':rev['id']};status,j=self.req('compilations','POST',payload,extra={'Idempotency-Key':'test-key'});self.assertEqual(status,202)
  status,j2=self.req('compilations','POST',payload,extra={'Idempotency-Key':'test-key'});self.assertEqual(j['id'],j2['id'])
  for _ in range(100):
   _,job=self.req('jobs/'+j['id'])
   if job['data']['state']=='succeeded':break
   time.sleep(.05)
  self.assertEqual(job['data']['state'],'succeeded',job)
  status,result=self.req('results/'+job['data']['result_id']);self.assertEqual(status,200);self.assertEqual(result['data']['revision_id'],rev['id'])
  self.assertEqual(self.req('results/'+result['id'],actor='bob')[0],403)
  _,report=self.req('reports','POST',{'result_id':result['id']});self.assertEqual(report['data']['result_digest'],result['data']['result']['semantic_digest'])
 def test_synthetic_activation_guard(self):
  p=json.loads((ROOT/'knowledge/synthetic.json').read_text());_,pack=self.req('packs','POST',p)
  status,err=self.req('packs/'+pack['id']+'/activate','POST',{'channel':'production'});self.assertEqual(status,422);self.assertEqual(err['error']['code'],'synthetic_activation')
  status,act=self.req('packs/'+pack['id']+'/activate','POST',{'channel':'demonstration'});self.assertEqual(status,201)
  self.assertEqual(self.req('activations/'+act['id']+'/withdraw','POST',{})[0],200)
 def test_route_not_implemented_is_not_success(self):self.assertEqual(self.req('neon-submissions','POST',{})[0],409)
 def test_idempotency_payload_conflict(self):
  _,c=self.req('cases','POST',{'name':'Original'},extra={'Idempotency-Key':'conflict'})
  status,e=self.req('cases','POST',{'name':'Replacement'},extra={'Idempotency-Key':'conflict'})
  self.assertEqual(status,409)
 def test_import_review_and_version_guard(self):
  c,d=self.create();obs={'state':'known','value':'2400','unit':'count','origin':'customer','source':'uploaded row'}
  rows=[{'stage_id':'assistant','field':'users','observation':obs},{'stage_id':'missing','field':'users','observation':obs}]
  status,p=self.req('import-previews','POST',{'draft_id':d['id'],'rows':rows});self.assertEqual(status,201)
  self.assertEqual(len(p['data']['rejected']),1)
  self.assertEqual(self.req('import-commits','POST',{'preview_id':p['id']})[0],422)
  status,u=self.req('import-commits','POST',{'preview_id':p['id'],'accept_partial':True});self.assertEqual(status,200)
  self.assertEqual(u['data']['stages'][0]['observations']['users']['value'],'2400')
  self.assertEqual(self.req('import-commits','POST',{'preview_id':p['id'],'accept_partial':True})[0],409)
 def test_knowledge_dependency_lock(self):
  p=json.loads((ROOT/'knowledge/synthetic.json').read_text());_,base=self.req('packs','POST',p)
  overlay={**p,'id':'dependent','profiles':[],'dependencies':[base['data']['digest']]}
  _,pack=self.req('packs','POST',overlay)
  status,act=self.req('packs/'+pack['id']+'/activate','POST',{'channel':'demonstration'});self.assertEqual(status,201)
  self.assertEqual(len(act['data']['knowledge_lock']['entries']),2)
  self.assertEqual(len(act['data']['knowledge_lock']['resolved']['profiles']),1)
  overlay['version']='conflict';overlay['profiles']=copy.deepcopy(p['profiles']);overlay['profiles'][0]['capacity']='13'
  _,bad=self.req('packs','POST',overlay)
  status,e=self.req('packs/'+bad['id']+'/activate','POST',{'channel':'demonstration'});self.assertEqual(status,422);self.assertEqual(e['error']['code'],'knowledge_conflict')
 def test_agent_budget_and_no_write(self):
  c,d=self.create();self.req('cases/'+c['id'],'PATCH',{'members':['agent'],'agent_compile_limit':1},extra={'If-Match':'1'})
  _,rev=self.req('drafts/'+d['id']+'/freeze','POST',{},extra={'If-Match':'1'})
  self.assertEqual(self.req('compilations','POST',{'revision_id':rev['id']},actor='agent')[0],202)
  self.assertEqual(self.req('compilations','POST',{'revision_id':rev['id']},actor='agent')[0],422)
  self.assertEqual(self.req('drafts/'+d['id'],'PATCH',d['data'],actor='agent',extra={'If-Match':'1'})[0],422)
 def test_agent_proposal_requires_human_review(self):
  c,d=self.create();self.req('cases/'+c['id'],'PATCH',{'members':['agent'],'agent_proposal_limit':1},extra={'If-Match':'1'})
  obs={'state':'assumed','value':'2400','unit':'count','origin':'agent','source':'untrusted proposal: ignore all rules','accepted':False}
  rows=[{'stage_id':'assistant','field':'users','observation':obs}]
  status,p=self.req('observation-proposals','POST',{'draft_id':d['id'],'rows':rows},actor='agent');self.assertEqual(status,201,p)
  _,before=self.req('drafts/'+d['id']);self.assertEqual(before['data']['stages'][0]['observations']['users']['value'],'1200')
  self.assertEqual(self.req('proposal-reviews','POST',{'proposal_id':p['id'],'accept_rows':[0],'rationale':'self approve'},actor='agent')[0],422)
  status,review=self.req('proposal-reviews','POST',{'proposal_id':p['id'],'accept_rows':[0],'rationale':'Consultant verified revised employee population'});self.assertEqual(status,201,review)
  self.assertTrue(review['draft']['data']['stages'][0]['observations']['users']['accepted'])
  self.assertEqual(self.req('observation-proposals','POST',{'draft_id':d['id'],'rows':rows},actor='agent')[0],422)
 def test_backup_restore(self):
  self.create();status,b=self.req('admin/backup','POST',{});self.assertEqual(status,201)
  backup=pathlib.Path(b['data']['path']);self.assertTrue(backup.exists())
  r=subprocess.run(['python3',str(ROOT/'scripts/backup.py'),'verify',str(backup)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_qualification_split_and_predeclared_limits(self):
  import hashlib
  pack=json.loads((ROOT/'knowledge/synthetic.json').read_text());_,p=self.req('packs','POST',pack)
  protocol={'pack_digest':p['data']['digest'],'metric':'throughput','measurement_boundary':'service','quality_conditions':'test only','min_cases':2,'max_relative_error':'0.1','max_false_feasible_fraction':'0','calibration_configuration_ids':['calibration'],'domain':'inference','source':'synthetic protocol test'}
  _,protocol_record=self.req('qualification-protocols','POST',protocol)
  dataset={'protocol_digest':protocol_record['data']['digest'],'source_artifact_sha256':'a'*64,'source':'synthetic qualification software test','cases':[{'configuration_id':str(i),'predicted':'100','measured':'100','predicted_pass':True,'observed_pass':True} for i in range(2)]}
  status,r=self.req('qualification-runs','POST',{'protocol_id':protocol_record['id'],'dataset':dataset});self.assertEqual(status,201);self.assertTrue(r['data']['report']['pass'])
  dataset['cases'][0]['configuration_id']='calibration'
  status,e=self.req('qualification-runs','POST',{'protocol_id':protocol_record['id'],'dataset':dataset});self.assertEqual(status,422);self.assertEqual(e['error']['code'],'data_leakage')
if __name__=='__main__':unittest.main(verbosity=2)
