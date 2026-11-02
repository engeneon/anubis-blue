#!/usr/bin/env python3
"""Repeatable software verification. Live model quality and human usability remain separate gates."""
import argparse,datetime,hashlib,json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1];out=root/'implementation/copilot';out.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--ui',action='store_true');a=p.parse_args()
commands=[('build',['cmake','--build','--preset','local','-j4']),('ui-build',['npm','run','build']),('core',['ctest','--test-dir','build','--output-on-failure']),('copilot',[sys.executable,'tests/test_copilot.py']),('interpretation',[sys.executable,'tests/test_interpretation.py']),('architecture-scenarios',[sys.executable,'tests/test_usability.py']),('guided-api',[sys.executable,'tests/test_usability_api.py']),('planning',[sys.executable,'tests/test_planning.py']),('network',[sys.executable,'tests/test_network_planning.py']),('system',[sys.executable,'tests/test_system.py']),('mcp',[sys.executable,'tests/test_mcp.py']),('diagram',['node','tests/test_system_diagram.mjs'])]
if a.ui:commands.append(('browser',['npm','run','test:ui']))
checks=[]
for name,argv in commands:
 print('Running '+name,flush=True);r=subprocess.run(argv,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);log=out/(name+'.log');log.write_text(r.stdout);checks.append(dict(name=name,argv=argv,returncode=r.returncode,log=str(log.relative_to(root)),sha256=hashlib.sha256(r.stdout.encode()).hexdigest()))
 if r.returncode:print(r.stdout);break
report=dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=checks,software_passed=len(checks)==len(commands) and all(c['returncode']==0 for c in checks),live_model_qualified=False,human_usability_target_validated=False,production_release_approved=False)
(out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');sys.exit(0 if report['software_passed'] else 1)
