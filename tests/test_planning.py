"""Focused planning checks with independent equations, not performance qualification."""
import unittest,json,subprocess,copy,pathlib
from fractions import Fraction as F
ROOT=pathlib.Path(__file__).resolve().parents[1]
def fixture(n):return json.loads((ROOT/f'tests/fixtures/{n}-planning.json').read_text())
def run(w):
 import tempfile
 with tempfile.NamedTemporaryFile(mode='w',suffix='.json') as f:
  json.dump(w,f);f.flush();p=subprocess.run([str(ROOT/'build/anubis'),'compile',f.name],capture_output=True,text=True)
  if p.returncode:raise ValueError(p.stdout+p.stderr)
  return json.loads(p.stdout)
class Planning(unittest.TestCase):
 def test_stories_and_units(self):
  for n,g in [('meridian',8),('harbor',176),('aster',16)]:
   r=run(fixture(n));p=r['planning'];self.assertEqual(p['raw_gpus'],g);self.assertEqual(p['initial_gpus'],256);self.assertEqual(p['status'],'conditional');self.assertEqual(r['candidates'][-1]['id'],'planning:factory')
  p=run(fixture('aster'))['planning'];self.assertAlmostEqual(float(p['ingress_Gbps']),60e12/(12*3600)*8/1e9*1.2,places=5)
 def test_workload_instances(self):
  for name,expected,low,high in [('meridian',32,32,32),('harbor',1,1,1),('aster',16,10,16)]:
   c=run(fixture(name))['planning']['workload_capacity']
   for key in ['minimum_architecture','selected_architecture']:
    a=c[key];self.assertTrue(a['supports_one_instance_compute']);self.assertEqual(a['equivalent_instances_compute'],expected)
    self.assertEqual((a['downside_instances_compute'],a['upside_instances_compute']),(low,high))
   self.assertIsNone(c['tenant_limit'])
  w=fixture('meridian');w['stages'][0]['observations']['users']['value']='121000'
  c=run(w)['planning']['workload_capacity'];self.assertFalse(c['minimum_architecture']['supports_one_instance_compute']);self.assertTrue(c['selected_architecture']['supports_one_instance_compute'])
  w['planning']['minimum_service_fraction']='.5';w['planning']['accept_capacity_shortfall']=True
  c=run(w)['planning']['workload_capacity']['selected_architecture'];self.assertIsNot(c['supports_one_instance_compute'],True);self.assertIn(c['equivalent_instances_compute'],[0,None])
  w['planning']['assumptions_accepted']=False
  c=run(w)['planning']['workload_capacity'];self.assertIsNone(c['selected_architecture']['equivalent_instances_compute'])
 def test_training_equation(self):
  p=run(fixture('aster'))['planning'];s=next(x for x in p['stage_calculations'] if x['stage_id']=='campaign')
  expected=F(2250)*F(35,100)*10**12*8/(6*30*10**9)
  self.assertAlmostEqual(float(s['capacity_per_replica']),float(expected),places=5)
  self.assertEqual(F(s['required_GB_per_gpu']),F(30*16,8)+32+8)
 def test_memory_and_acceptance(self):
  w=fixture('meridian');w['stages'][0]['planning']['context_tokens']=1000000
  self.assertEqual(run(w)['planning']['status'],'fail');self.assertFalse(run(w)['candidates'])
  w=fixture('meridian');w['planning']['assumptions_accepted']=False
  self.assertEqual(run(w)['planning']['status'],'unknown');self.assertFalse(run(w)['candidates'])
 def test_monotonic_and_replay(self):
  w=fixture('meridian');p=run(w);w['stages'].reverse();w['scenarios'].reverse();self.assertEqual(p,run(w))
  next(s for s in w['stages'] if s['id']=='assistant')['observations']['users']['value']='12000'
  self.assertGreaterEqual(run(w)['planning']['raw_gpus'],p['planning']['raw_gpus'])
 def test_anchor_boundaries_and_lower_choice(self):
  # Increase demand until it crosses the first architecture anchor.
  w=fixture('harbor');w['scenarios'][0]['multiplier']='10'
  p=run(w)['planning'];self.assertGreater(p['raw_gpus'],256)
  self.assertTrue(p['initial_gpus']>=p['raw_gpus'] or p['selected_anchor'] is None)
  w['planning']['minimum_service_fraction']='.5'
  with self.assertRaises(ValueError):run(w)
  w['planning']['accept_capacity_shortfall']=True
  q=run(w)['planning'];self.assertTrue(q['selected_anchor'] is None or q['initial_gpus']>=q['raw_gpus']*.5)
  w['scenarios'][0]['multiplier']='10000';q=run(w)['planning'];self.assertIsNone(q['selected_anchor']);self.assertFalse(run(w)['candidates'])
 def test_exact_anchor_and_transition(self):
  for users,raw,anchor in [('120000',256,256),('121000',264,512),('240000',512,512),('241000',520,1024)]:
   w=fixture('meridian');w['stages'][0]['observations']['users']['value']=users;p=run(w)['planning']
   self.assertEqual((p['raw_gpus'],p['initial_gpus']),(raw,anchor))
 def test_inference_memory_oracle(self):
  p=run(fixture('meridian'))['planning'];s=p['stage_calculations'][0]
  kv=F(2*32*8*128*2*8192*32,10**9)
  self.assertAlmostEqual(float(s['required_GB_per_gpu']),float(16+kv+8),places=5)
 def test_band_only_changes_sensitivity(self):
  w=fixture('harbor');a=run(w)['planning'];w['planning']['sensitivity_percent']='10';b=run(w)['planning']
  self.assertEqual(a['initial_gpus'],b['initial_gpus']);self.assertEqual(a['raw_gpus'],b['raw_gpus']);self.assertGreaterEqual(a['downside_gpus'],b['downside_gpus'])
 def test_invalid_configuration(self):
  for k,v in [('compute_efficiency','0'),('memory_efficiency','2'),('sensitivity_percent','100')]:
   w=fixture('meridian');w['planning'][k]=v
   with self.assertRaises(ValueError):run(w)
 def test_hardware_comparison(self):
  w=fixture('meridian');w['stages'][0]['observations']['users']['value']='24000'
  p=run(w)['planning'];rows={h['platform']:h for h in p['hardware_comparison']}
  self.assertEqual(set(rows),{'HGX_B300','HGX_B200','HGX_H200'})
  self.assertEqual(rows['HGX_B300']['raw_gpus'],p['raw_gpus'])
  self.assertGreater(rows['HGX_H200']['raw_gpus'],rows['HGX_B200']['raw_gpus'])
  for h in rows.values():
   self.assertEqual(h['status'],'conditional');self.assertEqual(h['raw_gpus']%8,0)
   self.assertNotIn('initial_gpus',h)
  w['stages'][0]['planning']['context_tokens']=32768
  rows={h['platform']:h for h in run(w)['planning']['hardware_comparison']}
  self.assertEqual(rows['HGX_H200']['status'],'fail')
  self.assertEqual(rows['HGX_B300']['status'],'conditional')
 def test_originals_stay_incomplete(self):
  w=json.loads((ROOT/'tests/fixtures/meridian.json').read_text());r=run(w);self.assertNotIn('planning',r);self.assertEqual(r['candidates'],[])
if __name__=='__main__':unittest.main()
