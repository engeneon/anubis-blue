#!/usr/bin/env python3
"""Repeatable 16-story incomplete-input boundary check, not hardware qualification."""
import json,pathlib,subprocess,tempfile
root=pathlib.Path(__file__).resolve().parents[1]
scenarios=json.loads((root/'tests/fixtures/architecture-scenarios.json').read_text())
rows=[]
def run(binary,data):
 with tempfile.NamedTemporaryFile(mode='w',suffix='.json') as f:
  json.dump(data,f);f.flush()
  args=[str(root/'build'/binary),str(root),f.name] if binary=='anubis_guided_driver' else [str(root/'build/anubis'),'compile',f.name]
  return json.loads(subprocess.check_output(args,text=True))
for s in scenarios:
 components=[]
 for a in s['answers']['activities']:
  ans=a['answers'];pattern=next((p for p in ['training','adaptation','generation','stream','agent','retrieval','batch','direct'] if ans.get({'retrieval':'search','direct':'text'}.get(p,p))=='yes'),'other')
  if ans.get('indexing')=='yes' and ans.get('text')!='yes':pattern='other'
  components.append({'name':a['name'],'pattern':pattern,'location':a['location'] if a['location']!='mixed' else 'unknown','relationship':a['relationship'],'rate':'','model':'dense8b','retrieval':'unknown'})
 intake={'name':s['name'],'components':components,'overlap':s['answers']['overlap'],'tenancy':s['answers']['tenancy'] if s['answers']['tenancy']!='unknown' else 'single','accepted':True}
 w=run('anubis_guided_driver',intake)
 assert w==run('anubis_guided_driver',intake),s['id']
 result=run('anubis',w)
 assert result['planning']['status']=='unknown',s['id']
 assert not result['candidates'],s['id']
 rows.append({'id':s['id'],'name':s['name'],'passed':True,'planning_status':'unknown','candidates':0})
report={'scope':'All 16 fixture stories transformed with deliberately incomplete numerical intake. Checks deterministic transformation, unknown planning and absence of a complete candidate. Does not certify live interpretation, each narrative acceptance criterion or hardware performance.','scenarios':rows}
p=root/'testing-evidence/scenario-catalogue.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(report,indent=2)+'\n')
print('16 of 16 incomplete-input boundary checks passed.')
