import unittest
from test_usability import intake,transform,compile_w
class NetworkPlanning(unittest.TestCase):
 def plan(self,**network):
  b=intake();b['network']=network;return compile_w(transform(b))['planning']
 def test_initial_load_and_overlap(self):
  p=self.plan(initial_tb='100',load_hours='24',daily_ingest_gb='0',daily_egress_gb='0',utilization='0.8',overlap='no')
  n=p['networks'];self.assertAlmostEqual(float(n['external_customer_datacenter']['initial_load_link_Gbps']),13.888889,places=5)
  self.assertEqual(n['north_south']['ingress_lower_bound_Gbps'],n['external_customer_datacenter']['required_ingress_lower_bound_Gbps'])
  self.assertEqual(p['raw_gpus'],8)
 def test_overlap_adds_once(self):
  a=self.plan(initial_tb='100',load_hours='24',daily_ingest_gb='1000',overlap='no')['networks']['external_customer_datacenter'];b=self.plan(initial_tb='100',load_hours='24',daily_ingest_gb='1000',overlap='yes')['networks']['external_customer_datacenter']
  self.assertAlmostEqual(float(b['required_ingress_lower_bound_Gbps'])-float(a['required_ingress_lower_bound_Gbps']),float(a['steady_ingress_lower_bound_Gbps']),places=5)
 def test_dedicated_storage_and_direction(self):
  n=self.plan(storage_read_gbps='40',storage_write_gbps='10',utilization='0.8',ew_per_gpu_gbps='100')['networks'];self.assertTrue(n['storage']['dedicated']);self.assertFalse(n['storage']['converged']);self.assertEqual(n['storage']['read_link_lower_bound_Gbps'],'60');self.assertEqual(n['storage']['write_link_lower_bound_Gbps'],'15');self.assertEqual(n['east_west']['per_gpu_link_lower_bound_Gbps'],'150')
 def test_unknown_network_does_not_invent_rate_or_block_gpu(self):
  p=self.plan();self.assertEqual(p['raw_gpus'],8);self.assertIsNone(p['networks']['external_customer_datacenter']['initial_load_link_Gbps']);self.assertIsNone(p['networks']['storage']['read_link_lower_bound_Gbps'])
 def test_storage_uses_declared_stage_rates(self):
  b=intake(storage_tb="1");w=transform(b);w["stages"][-1]["observations"]["read_rate"]={"state":"estimated","value":"1","unit":"GB/s","source":"test","origin":"customer","accepted":True};n=compile_w(w)["planning"]["networks"];self.assertEqual(n["storage"]["read_payload_Gbps"],"8")
 def test_invalid_inputs_rejected(self):
  for n in [dict(initial_tb='-1'),dict(load_hours='0'),dict(utilization='0'),dict(utilization='2'),dict(storage_read_gbps='NaN'),dict(overlap='maybe')]:
   with self.assertRaises(ValueError):self.plan(**n)
if __name__=='__main__':unittest.main(verbosity=2)
