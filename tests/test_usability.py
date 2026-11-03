"""Repeatable architecture-led transformation/engine acceptance. No browser automation."""
import copy,json,pathlib,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
def intake(pattern='direct',**kw):
 c=dict(name='Customer service',pattern=pattern,location='local',rate='100',model='dense8b',retrieval='external');c.update(kw)
 return dict(name='Acceptance engagement',components=[c],overlap='yes',tenancy='single',accepted=True)
def transform(b):
 with tempfile.NamedTemporaryFile(mode='w',suffix='.json') as f:
  json.dump(b,f);f.flush();r=subprocess.run([str(ROOT/'build/anubis_guided_driver'),str(ROOT),f.name],capture_output=True,text=True)
  if r.returncode:raise ValueError(r.stderr)
  return json.loads(r.stdout)
def compile_w(w):
 with tempfile.NamedTemporaryFile(mode='w',suffix='.json') as f:
  json.dump(w,f);f.flush();r=subprocess.run([str(ROOT/'build/anubis'),'compile',f.name],capture_output=True,text=True)
  if r.returncode:raise ValueError(r.stderr+r.stdout)
  return json.loads(r.stdout)
class Usability(unittest.TestCase):
 def test_01_new_engagement_to_estimate(self):
  w=transform(intake());r=compile_w(w);self.assertEqual(r['planning']['status'],'conditional');self.assertGreater(r['planning']['raw_gpus'],0)
 def test_02_library_support_boundaries(self):
  for p in ['direct','retrieval','agent','batch','training','stream','generation','adaptation','other']:
   w=transform(intake(p,calls='4',jobs='80000',window='8',tokens='90000000000',days='30'));r=compile_w(w)
   self.assertEqual(r['planning']['status'],'unknown' if p in ['stream','generation','adaptation','other'] else 'conditional',p)
 def test_03_composition_includes_local_retrieval(self):
  w=transform(intake('retrieval',retrieval='local'));self.assertEqual(len(w['stages']),2);r=compile_w(w);self.assertGreater(r['planning']['raw_gpus'],0);self.assertEqual(r['candidates'],[]);self.assertIsNone(r['planning']['selected_anchor'])
 def test_04_map_matches_compute_components(self):
  w=transform(intake());c=w['characterization']['components'][0];self.assertEqual(c['id'],w['stages'][0]['id']);self.assertEqual(c['name'],w['stages'][0]['name']);self.assertEqual(c['retrieval'],'external')
 def test_05_measurements_propagate(self):
  r=compile_w(transform(intake(rate='600',calls='3',input_tokens='1000',output_tokens='100')))
  self.assertEqual(float(r['planning']['stage_calculations'][0]['demand']),30)
 def test_06_alternative_demand_equivalence(self):
  a=compile_w(transform(intake(rate='600')));b=compile_w(transform(intake(demand_mode='users',users='1200',interval='120')))
  self.assertEqual(a['planning']['raw_gpus'],b['planning']['raw_gpus'])
 def test_07_refinement_changes_estimate(self):
  a=compile_w(transform(intake(rate='600')));b=compile_w(transform(intake(rate='60000')));self.assertGreater(b['planning']['raw_gpus'],a['planning']['raw_gpus'])
 def test_08_versioned_default_provenance(self):
  w=transform(intake());self.assertEqual(w['characterization']['pack_version'],'guided-1.0');self.assertEqual(len(w['characterization']['pack_digest']),64);self.assertEqual(w['stages'][0]['observations']['input_tokens']['origin'],'template');self.assertEqual(w['stages'][0]['observations']['rate']['origin'],'customer');blank=transform(intake(input_tokens='',output_tokens='',calls=''));self.assertEqual(blank['stages'][0]['observations']['input_tokens']['value'],'2000');self.assertEqual(blank['stages'][0]['observations']['input_tokens']['origin'],'template')
 def test_09_invalid_values_are_actionable(self):
  for c in [dict(rate='-1'),dict(calls='0'),dict(model='unlisted'),dict(storage_tb='-5'),dict(rate='NaN')]:
   with self.assertRaises(ValueError):transform(intake(**c))
 def test_10_unknown_demand_never_zero_estimate(self):
  for p,kw in [('direct',dict(rate='')),('agent',dict(calls=''))]:
   r=compile_w(transform(intake(p,**kw)));self.assertEqual(r['planning']['status'],'unknown');self.assertEqual(r['candidates'],[]);self.assertIsNone(r['planning']['selected_anchor'])
 def test_11_schedule_and_reservation(self):
  b=intake(rate='6000');b['components'].append(dict(b['components'][0],name='Second activity'));a=compile_w(transform(b));b['overlap']='no';c=compile_w(transform(b));self.assertEqual(a['planning']['raw_gpus'],2*c['planning']['raw_gpus']);b['components'][0]['dedicated']=True;self.assertEqual(compile_w(transform(b))['planning']['raw_gpus'],a['planning']['raw_gpus']);b['components'][1]['relationship']='alongside'
  with self.assertRaises(ValueError):transform(b)
 def test_12_anchor_separate_from_workload(self):
  p=compile_w(transform(intake()))['planning'];self.assertEqual(p['initial_gpus'],256);self.assertLess(p['raw_gpus'],256)
 def test_13_resource_drivers_and_growth(self):
  p=compile_w(transform(intake(storage_tb='8',growth_gb_day='40',horizon_days='100')))['planning'];self.assertEqual(float(p['storage'][0]['usable_bytes']),15e12);self.assertIsNone(p['storage'][0]['read_Bps']);self.assertGreater(float(p['ingress_Gbps']),0);self.assertEqual(len(p['hardware_comparison']),3)
 def test_14_handoff_candidate_and_partial_brief(self):
  r=compile_w(transform(intake()));self.assertEqual(r['candidates'][-1]['id'],'planning:factory');self.assertEqual(r['guided_context']['name'],'Acceptance engagement');r=compile_w(transform(intake('other')));self.assertEqual(r['candidates'],[]);self.assertIn('solver-specific',' '.join(r['guided_context']['characterization']['follow_up']))
 def test_15_customer_guide_contract(self):
  p=ROOT/'docs/usability-user-guide.html';self.assertTrue(p.exists());s=p.read_text().lower();self.assertNotIn('synthetic end-user',s);self.assertIn('new engagement',s);self.assertIn('appendix',s)
 def test_16_random_and_all_scenario_boundaries(self):
  scenarios=json.loads((ROOT/'tests/fixtures/architecture-boundary-scenarios.json').read_text());rows=[]
  for case in scenarios:
   b=intake();b['name']=case['name'];b['components']=[];b['overlap']=case['answers']['overlap'];b['tenancy']=case['answers']['tenancy'] if case['answers']['tenancy']!='unknown' else 'single'
   for a in case['answers']['activities']:
    ans=a['answers'];pattern=next((p for p in ['training','adaptation','generation','stream','agent','retrieval','batch','direct'] if ans.get({'retrieval':'search','direct':'text'}.get(p,p))=='yes'),'other')
    if ans.get('indexing')=='yes' and ans.get('text')!='yes':pattern='other'
    c=dict(name=a['name'],pattern=pattern,location=a['location'] if a['location']!='mixed' else 'unknown',relationship=a['relationship'],rate='',model='dense8b',retrieval='unknown');b['components'].append(c)
   w=transform(b);self.assertEqual(w,transform(b));r=compile_w(w);self.assertEqual(r['planning']['status'],'unknown');rows.append({'id':case['id'],'status':r['planning']['status'],'candidates':len(r['candidates'])})
  selection=json.loads((ROOT/'implementation/usability/random-scenario.json').read_text());self.assertEqual(selection['scenario']['id'],'S16');self.assertEqual(rows[15]['candidates'],0)
  (ROOT/'implementation/usability/scenario-validation.json').write_text(json.dumps(rows,indent=2))
if __name__=='__main__':unittest.main(verbosity=2)
