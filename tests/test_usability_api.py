"""HTTP regression checks for guided intake and unchanged downstream payloads."""
import unittest,time,urllib.request
import test_system
from test_usability import intake
class GuidedAPI(unittest.TestCase):
 setUpClass=classmethod(test_system.API.setUpClass.__func__)
 tearDownClass=classmethod(test_system.API.tearDownClass.__func__)
 req=test_system.API.req
 def test_catalog_assets_and_authorization(self):
  self.assertEqual(self.req('guided-catalog')[0],200)
  for asset,mime in [('readiness.js','javascript'),('guided.js','javascript'),('system-diagram.js','javascript'),('anubis-logo.png','image/png'),('user-guide.html','html')]:
   with urllib.request.urlopen(f'http://127.0.0.1:{self.port}/'+asset) as r:self.assertEqual(r.status,200);self.assertIn(mime,r.headers['Content-Type'])
  self.assertEqual(self.req('guided-workloads','POST',intake(),actor='reader')[0],403)
  self.assertEqual(self.req('guided-workloads','POST',intake(rate='bad'))[0],422)
 def test_saved_compile_and_handoff(self):
  status,w=self.req('guided-workloads','POST',intake());self.assertEqual(status,200,w)
  _,c=self.req('cases','POST',{'name':w['name']});_,d=self.req('cases/'+c['id']+'/drafts','POST',w)
  status,rev=self.req('drafts/'+d['id']+'/freeze','POST',{},extra={'If-Match':str(d['version'])});self.assertEqual(status,201,rev)
  _,j=self.req('compilations','POST',{'revision_id':rev['id']})
  for _ in range(100):
   _,job=self.req('jobs/'+j['id'])
   if job['data']['state'] in ['succeeded','failed']:break
   time.sleep(.05)
  self.assertEqual(job['data']['state'],'succeeded',job)
  _,r=self.req('results/'+job['data']['result_id']);self.assertEqual(r['data']['result']['planning']['raw_gpus'],8)
  status,p=self.req('neon-projections','POST',{'result_id':r['id'],'mapping':{'candidate_id':'planning:factory','platform':'HGX_B300','network_fabric':'Spectrum-X'}})
  self.assertEqual(status,201,p);payload=p['data']['payload'];self.assertEqual(payload['requirements']['target_gpu_count'],256);self.assertEqual(payload['requirements']['platform'],'HGX_B300');self.assertIn('companion_requirements',p['data'])
  ledger={v['field']:v for v in p['data']['mapping_ledger']}
  for field in ['north_south','external_customer_datacenter','dedicated_storage_network']:self.assertEqual(ledger[field]['mode'],'brief_only')
  self.assertFalse(p['data']['companion_requirements']['networks']['storage']['converged'])
  w['name']='Later draft name';self.req('drafts/'+d['id'],'PATCH',w,extra={'If-Match':str(d['version'])});_,old=self.req('results/'+r['id']);self.assertEqual(old['data']['result']['guided_context']['name'],'Acceptance engagement')
if __name__=='__main__':unittest.main(verbosity=2)
