#!/usr/bin/env python3
"""Run bound software checks and retain honest command evidence; never approve release gates."""
import argparse,datetime,hashlib,json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--ui',action='store_true');a=p.parse_args()
commands=[['python3','scripts/validate_implementation_plan.py'],['python3','scripts/verify_source_locks.py'],['cmake','--build','--preset','local','-j4'],['ctest','--test-dir','build','--output-on-failure'],['npm','run','check'],['npm','run','build'],['python3','tests/test_planning.py'],['python3','tests/test_system.py'],['python3','tests/test_mcp.py']]
if a.ui:commands.append(['npm','run','test:ui'])
evidence=root/'implementation/release-evidence';evidence.mkdir(exist_ok=True);records=[]
for i,cmd in enumerate(commands):
 print('Running: '+' '.join(cmd),flush=True)
 r=subprocess.run(cmd,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 name=f'check-{i+1:02}.log';(evidence/name).write_text(r.stdout)
 records.append({'argv':cmd,'returncode':r.returncode,'log':name,'sha256':hashlib.sha256(r.stdout.encode()).hexdigest()})
 if r.returncode:print(r.stdout);break
report={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':records,'all_requested_checks_passed':len(records)==len(commands) and all(r['returncode']==0 for r in records),'empirical_qualification':False,'release_approval':False}
(evidence/'software-checks.json').write_text(json.dumps(report,indent=2)+'\n')
sys.exit(0 if report['all_requested_checks_passed'] else 1)
