"""GPU-complete scenario acceptance and minimum-input preflight regressions."""
import copy,json,math,pathlib,subprocess,tempfile,time,unittest
from fractions import Fraction
from test_usability import ROOT,intake,transform,compile_w
import test_system
CASES=json.loads((ROOT/'tests/fixtures/architecture-scenarios.json').read_text())
def readiness(b):
 with tempfile.NamedTemporaryFile(mode='w',suffix='.json') as f:
  json.dump(b,f);f.flush()
  p=subprocess.run([str(ROOT/'build/anubis_guided_driver'),str(ROOT),f.name,'--readiness'],capture_output=True,text=True,check=True)
  return json.loads(p.stdout)
class Readiness(unittest.TestCase):
 def test_missing_inputs_are_named(self):
  for pattern,fields in [('direct',{'rate'}),('agent',{'rate','calls'}),('batch',{'jobs','window'}),('training',{'tokens','days'}),('stream',{'sizing_method'})]:
   r=readiness(intake(pattern,rate=''));self.assertFalse(r['ready']);self.assertTrue(fields <= {v['field'] for v in r['missing']})
 def test_alternative_demand_and_defaults(self):
  self.assertTrue(readiness(intake(demand_mode='users',rate='',users='120',interval='30'))['ready'])
  self.assertTrue(readiness(intake())['ready'])
  for changes in [dict(rate='NaN'),dict(rate='0'),dict(calls='.5'),dict(input_tokens='9000'),dict(location='unknown'),dict(model='unlisted'),dict(pattern='retrieval',retrieval='local')]:
   self.assertFalse(readiness(intake(**changes))['ready'],changes)
 def test_outside_only_does_not_invent_local_gpus(self):
  self.assertFalse(readiness(intake(location='external'))['ready'])
  r=compile_w(transform(intake(location='external')));self.assertEqual(r['candidates'],[])
 def test_reference_requires_each_matching_input_and_acceptance(self):
  b=copy.deepcopy(CASES[4]['planning_input'])
  for field in ['reference_demand','reference_memory','reference_gpus','reference_h200','reference_b200','reference_b300','reference_source','reference_unit','reference_independent','reference_accepted']:
   bad=copy.deepcopy(b);del bad['components'][0][field];r=readiness(bad)
   self.assertFalse(r['ready'],field);self.assertIn(field,{v['field'] for v in r['missing']})
  for value in ['0','3','9','1025','1.5']:
   bad=copy.deepcopy(b);bad['components'][0]['reference_gpus']=value;self.assertFalse(readiness(bad)['ready'])
 def test_reference_profile_and_incomplete_draft(self):
  b=copy.deepcopy(CASES[4]['planning_input']);b['architecture']='SX-HGXB300-DP-ENT-1.0.0';self.assertTrue(readiness(b)['ready'])
  del b['components'][0]['reference_h200'];r=compile_w(transform(b));self.assertEqual(r['candidates'],[]);self.assertEqual(r['planning']['status'],'unknown')
 def test_reference_arithmetic_and_sensitivity_independent_oracle(self):
  b=copy.deepcopy(CASES[4]['planning_input']);p=compile_w(transform(b))['planning']
  c=b['components'][0]
  self.assertNotIn('model',p['stage_calculations'][0]['assumptions'])
  for h in p['hardware_comparison']:
   cap=Fraction(c['reference_'+h['platform'].split('_')[1].lower()]);demand=Fraction(c['reference_demand']);group=int(c['reference_gpus'])
   oracle=lambda factor:math.ceil(math.ceil(demand/(cap*factor))*group/8)*8
   self.assertEqual(h['raw_gpus'],oracle(Fraction(1)))
   self.assertEqual(h['upside_gpus'],oracle(Fraction(13,10)))
   self.assertEqual(h['downside_gpus'],oracle(Fraction(7,10)))
  self.assertIn('Reference GPU capacity',' '.join(p['networks']['follow_up']))
 def test_reference_memory_infeasibility_is_not_a_candidate(self):
  b=copy.deepcopy(CASES[4]['planning_input']);b['components'][0]['reference_memory']='1000'
  r=compile_w(transform(b));self.assertEqual(r['planning']['status'],'fail');self.assertEqual(r['candidates'],[])
 def test_reference_group_schedule_and_reserved_capacity(self):
  b=copy.deepcopy(CASES[4]['planning_input']);b['components'].append(dict(b['components'][0],name='Second pool'))
  combined=compile_w(transform(b))['planning']['raw_gpus'];b['overlap']='no'
  self.assertEqual(compile_w(transform(b))['planning']['raw_gpus']*2,combined)
  b['components'][0]['dedicated']=True;self.assertEqual(compile_w(transform(b))['planning']['raw_gpus'],combined)
 def test_all_sixteen_positive_comparisons_and_candidate(self):
  self.assertEqual(len(CASES),16)
  for c in CASES:
   with self.subTest(scenario=c['id']):
    self.assertTrue(readiness(c['planning_input'])['ready'])
    w=transform(c['planning_input']);self.assertEqual(w,transform(c['planning_input']))
    r=compile_w(w);p=r['planning'];self.assertEqual(p['status'],'conditional');self.assertEqual(p['gaps'],[])
    self.assertTrue(any(a['id']=='planning:factory' for a in r['candidates']))
    self.assertEqual(len(p['hardware_comparison']),3)
    for h in p['hardware_comparison']:
     self.assertEqual(h['raw_gpus'],c['expected_gpu_counts'][h['platform']]);self.assertEqual(h['status'],'conditional');self.assertGreater(h['raw_gpus'],0);self.assertEqual(h['raw_gpus']%8,0)
    if c['id'] in ['S02','S13']:self.assertEqual(p['storage'],[])
class ReadinessAPI(unittest.TestCase):
 setUpClass=classmethod(test_system.API.setUpClass.__func__)
 tearDownClass=classmethod(test_system.API.tearDownClass.__func__)
 req=test_system.API.req
 def test_preflight_http_and_recovery(self):
  status,r=self.req('guided-readiness','POST',intake(rate=''));self.assertEqual(status,200);self.assertFalse(r['ready']);self.assertEqual(r['missing'][0]['field'],'rate')
  status,r=self.req('guided-readiness','POST',intake());self.assertEqual(status,200);self.assertTrue(r['ready'])
 def test_reference_survives_copilot_reopen_but_cannot_be_invented(self):
  b=copy.deepcopy(CASES[4]['planning_input']);_,w=self.req('guided-workloads','POST',b)
  _,c=self.req('cases','POST',{'name':w['name']});_,d=self.req('cases/'+c['id']+'/drafts','POST',w)
  status,session=self.req('copilot-sessions','POST',{'case_id':c['id'],'draft_id':d['id'],'classification':'public'});self.assertEqual(status,201,session)
  status,p=self.req('copilot-sessions/'+session['id']+'/proposals','POST',{'question':'Preserve reference','changes':[]});self.assertEqual(status,201,p)
  components=copy.deepcopy(b['components']);components[0]['reference_b300']='100000'
  status,p=self.req('copilot-sessions/'+session['id']+'/proposals','POST',{'question':'Change reference','changes':[{'field':'components','value':components,'basis':'planning_assumption','source_id':'','quote':'','reason':'invented capacity'}]});self.assertEqual(status,422,p)
 def test_all_sixteen_saved_compilations_and_handoffs(self):
  rows=[]
  for case in CASES:
   with self.subTest(scenario=case['id']):
    status,discovery=self.req('characterizations','POST',case['answers']);self.assertEqual(status,200,discovery);self.assertEqual(discovery['patterns'],case['expected_patterns'])
    status,w=self.req('guided-workloads','POST',case['planning_input']);self.assertEqual(status,200,w)
    _,c=self.req('cases','POST',{'name':w['name']});_,d=self.req('cases/'+c['id']+'/drafts','POST',w)
    status,rev=self.req('drafts/'+d['id']+'/freeze','POST',{},extra={'If-Match':str(d['version'])});self.assertEqual(status,201,rev)
    _,j=self.req('compilations','POST',{'revision_id':rev['id']})
    for _ in range(100):
     _,job=self.req('jobs/'+j['id'])
     if job['data']['state'] in ['succeeded','failed']:break
     time.sleep(.05)
    self.assertEqual(job['data']['state'],'succeeded',job)
    _,r=self.req('results/'+job['data']['result_id']);p=r['data']['result']['planning']
    status,projection=self.req('neon-projections','POST',{'result_id':r['id'],'mapping':{'candidate_id':'planning:factory','platform':'HGX_B300','network_fabric':'Spectrum-X'}})
    self.assertEqual(status,201,projection);self.assertEqual(projection['data']['payload']['requirements']['target_gpu_count'],p['initial_gpus'])
    rows.append(dict(id=case['id'],name=case['name'],status=p['status'],gpu_counts={h['platform']:h['raw_gpus'] for h in p['hardware_comparison']},factory_gpus=p['initial_gpus'],handoff=True,evidence_basis=p['evidence_basis']))
  folder=ROOT/'testing-evidence/gpu-readiness';folder.mkdir(parents=True,exist_ok=True)
  (folder/'scenario-results.json').write_text(json.dumps({'scope':'Deterministic calculation and local handoff contract. Fictional planning inputs, not performance qualification.','scenarios':rows},indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
