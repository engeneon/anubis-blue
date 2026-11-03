"""Saved-result narration. Provider fixtures validate plumbing, not live language quality."""
import json,time,copy,pathlib,unittest
import test_copilot as harness
from test_gpu_readiness import CASES
# Reuse fixture transport and isolation, without inheriting unrelated test methods.
class Explanations(unittest.TestCase):
 setUpClass=classmethod(harness.Copilot.setUpClass.__func__)
 tearDownClass=classmethod(harness.Copilot.tearDownClass.__func__)
 req=harness.Copilot.req;good=harness.Copilot.good;wait=harness.Copilot.wait;profile=harness.Copilot.profile;qualify=harness.Copilot.qualify
 def saved(self,b):
  w=self.good('guided-workloads','POST',b);c=self.good('cases','POST',{'name':w['name']});d=self.good('cases/'+c['id']+'/drafts','POST',w);rev=self.good('drafts/'+d['id']+'/freeze','POST',{},extra={'If-Match':str(d['version'])});j=self.wait(self.good('compilations','POST',{'revision_id':rev['id']}));return self.good('results/'+j['data']['result_id'])
 def explain(self,r,profile=None):
  e=self.good('copilot-explanations','POST',{'result_id':r['id'],'profile_id':profile['id'] if profile else ''})
  return self.good('copilot-explanations/'+self.wait(e)['data']['explanation_id']) if e['type']=='job' else e
 def test_all_sixteen_saved_result_narratives(self):
  p=self.profile(model='explanation');self.qualify(p);rows=[]
  for case in CASES:
   r=self.saved(case['planning_input']);before=copy.deepcopy(r);e=self.explain(r,p)
   self.assertEqual(e['data']['prompt_version'],'explanation-1.0');self.assertTrue(e['data']['prompt_digest']);self.assertEqual(e['data']['mode'],'model_assisted',e);self.assertEqual(self.good('results/'+r['id']),before)
   for s in e['data']['sections']:self.assertIn(e['data']['packet']['facts'][s['id']],s['text']);self.assertNotIn('{{',s['text'])
   self.assertEqual(len(self.good('copilot-explanations/'+r['id']+'/history')),1)
   rows.append({'id':case['id'],'mode':e['data']['mode'],'unchanged_result':True,'sections':len(e['data']['sections'])})
  out=pathlib.Path('testing-evidence/explanations');out.mkdir(parents=True,exist_ok=True);(out/'fixture-scenarios.json').write_text(json.dumps(rows,indent=2)+'\n')
 def test_unresolved_and_memory_failure_explanations(self):
  for index,change in [(0,{'rate':''}),(4,{'reference_memory':'1000'})]:
   b=copy.deepcopy(CASES[index]['planning_input']);b['components'][0].update(change);r=self.saved(b);e=self.explain(r);self.assertIn('not available',e['data']['packet']['facts']['outcome'])
 def test_untrusted_quantities_fall_back(self):
  p=self.profile(model='explanation_bad');self.qualify(p);r=self.saved(CASES[0]['planning_input']);e=self.explain(r,p);self.assertEqual(e['data']['mode'],'deterministic');self.assertIn('fallback_reason',e['data']);self.assertNotIn('99999',' '.join(s['text'] for s in e['data']['sections']))
 def test_authorization_policy_projection_and_history(self):
  r=self.saved(CASES[0]['planning_input']);self.assertEqual(self.req('copilot-explanations','POST',{'result_id':r['id']},actor='bob')[0],403)
  self.assertEqual(self.req('copilot-explanations/'+r['id']+'/history',actor='bob')[0],403)
  p=self.profile(model='explanation',policy='public');self.qualify(p);self.assertEqual(self.req('copilot-explanations','POST',{'result_id':r['id'],'profile_id':p['id']})[0],422)
  pr=self.good('neon-projections','POST',{'result_id':r['id'],'mapping':{'candidate_id':'planning:factory','platform':'HGX_B300','network_fabric':'Spectrum-X'}})
  e=self.good('copilot-explanations','POST',{'result_id':r['id'],'projection_id':pr['id']});self.assertEqual(e['data']['packet']['projection_id'],pr['id'])
  other=self.saved(CASES[1]['planning_input']);self.assertEqual(self.req('copilot-explanations','POST',{'result_id':other['id'],'projection_id':pr['id']})[0],422)
if __name__=='__main__':unittest.main(verbosity=2)
