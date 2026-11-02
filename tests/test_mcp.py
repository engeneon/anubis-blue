import json,os,pathlib,subprocess,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class MCP(unittest.TestCase):
 def test_handshake_and_injected_tool_denial(self):
  messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'test','version':'1'}}},{'jsonrpc':'2.0','method':'notifications/initialized'}, {'jsonrpc':'2.0','id':2,'method':'tools/list'}, {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'activate_pack','arguments':{}}}, {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'read_result','arguments':{'result_id':'../../admin/backup'}}}]
  r=subprocess.run(['node',str(ROOT/'mcp/server.mjs')],input='\n'.join(json.dumps(x) for x in messages)+'\n',capture_output=True,text=True,env={**os.environ,'ANUBIS_AGENT_TOKEN':'test-no-network-token'})
  self.assertEqual(r.returncode,0,r.stderr);lines=[json.loads(x) for x in r.stdout.splitlines()]
  self.assertEqual(lines[0]['result']['protocolVersion'],'2025-06-18')
  self.assertEqual(len(lines[1]['result']['tools']),10)
  self.assertNotIn('apply_proposal',[t['name'] for t in lines[1]['result']['tools']])
  self.assertIn('error',lines[2]);self.assertIn('error',lines[3])
 def test_nonlocal_target_rejected(self):
  r=subprocess.run(['node',str(ROOT/'mcp/server.mjs')],input='',capture_output=True,text=True,env={**os.environ,'ANUBIS_AGENT_TOKEN':'test','ANUBIS_URL':'http://example.com'})
  self.assertNotEqual(r.returncode,0)
if __name__=='__main__':unittest.main(verbosity=2)
