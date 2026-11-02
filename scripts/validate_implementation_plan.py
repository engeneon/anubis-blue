"""Validate delivery-plan consistency, not runtime sizing accuracy."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'implementation/anubis-work-packages.json').read_text())
assert m['plan_version']=='1.2'
ps=m['packages']; assert [p['id'] for p in ps]==['D1','D2','D3','D4','D5']
body=(root/'implementation/plan-render-source.txt').read_text()
assert '[[WORK_PACKAGES]]' not in body
ids=[]
for i,p in enumerate(ps):
 assert p['depends_on']==([] if i==0 else [ps[i-1]['id']])
 assert f"### {p['id']} {p['title']}" in body
 assert p['owned_paths'] and p['scope'] and p['acceptance']
 for a in p['acceptance']:
  assert a['id'] in body and a['assertion'] in body
  ids.append(a['id'])
assert len(ids)==len(set(ids))==10
assert m['release_gates']['VALUE']=={'packages':[p['id'] for p in ps],'requires':[]}
assert m['execution_policy']==dict(reuse_existing_application=True,write_leases_required=False,separate_approval_identity_required=False,empirical_qualification_required=False)
coverage={'gpu_count':['D2-A01','D3-A01'],'resource_correctness':['D2-A02'],'capital_efficiency':['D3-A02'],'neon_handoff':['D4-A01','D4-A02'],'customer_value':['D5-A01','D5-A02'],'inputs_and_anchors':['D1-A01','D1-A02']}
assert set(ids)=={a for values in coverage.values() for a in values}
report=dict(plan_version='1.2',status='pass',scope='Plan structure and acceptance coverage only',steps=5,assertions=10,objective_coverage=coverage,runtime_status='not_accepted',limitations=['Implementation remains pending','Actual sizing and downstream design tool compatibility require the planned runtime checks'])
(root/'implementation/release-evidence/plan-v1.2-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: five ordered steps, ten unique assertions, objective coverage and no deferred gate dependencies')
