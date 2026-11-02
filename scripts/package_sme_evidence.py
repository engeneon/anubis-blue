from pathlib import Path
import json,shutil,hashlib,subprocess,platform,datetime
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables/sme-evaluation-2026-11-02';E=OUT/'evidence';(E/'software').mkdir(exist_ok=True);(E/'historical').mkdir(exist_ok=True)
validation=json.loads((ROOT/'implementation/copilot/validation.json').read_text());shutil.copy2(ROOT/'implementation/copilot/validation.json',E/'software/validation.json')
for c in validation['checks']:shutil.copy2(ROOT/c['log'],E/'software'/Path(c['log']).name)
for n in ['final-originals-checks.json','final-paraphrases-checks.json','final-multiturn.json','interpretation-delivery.json']:
 shutil.copy2(ROOT/'implementation/copilot'/n,E/'historical'/n)
shutil.copy2(ROOT/'implementation/release-evidence/planning-neon-roundtrip.json',E/'historical/downstream-local-roundtrip.json')
for src,dst in [('knowledge/planning.json','planning-catalog.json'),('knowledge/guided-intake.json','guided-catalog.json'),('knowledge/workload-interpretation.json','interpretation-catalog.json'),('dependency-locks/local-profile.json','toolchain-baseline.json')]:shutil.copy2(ROOT/src,E/dst)
# Only source and fictional test material. Never copy runtime state or environment files.
ref=OUT/'reference-source';ref.mkdir(exist_ok=True)
for name in ['src','third_party','tests','ui','knowledge','contracts','deploy','mcp','dependency-locks']:
 shutil.copytree(ROOT/name,ref/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('dist','__pycache__','*.sqlite','*.db','*.pyc'))
for name in ['CMakeLists.txt','CMakePresets.json','package.json','package-lock.json','playwright.config.ts']:shutil.copy2(ROOT/name,ref/name)
(ref/'scripts').mkdir(exist_ok=True)
for name in ['copy-ui.mjs','test-server.mjs','validate_copilot.py','generate_contracts.py','backup.py','sme_oracles.py','sme_clean_install.py','sme_capture.mjs']:
 shutil.copy2(ROOT/'scripts'/name,ref/'scripts'/name)
(ref/'docs').mkdir(exist_ok=True)
for name in ['usability-user-guide.html','copilot-operation.txt','local-operation.md','qualification-options.md','playbook-standard.txt','anubis-framework-v2.txt']:shutil.copy2(ROOT/'docs'/name,ref/'docs'/name)
for group in ['copilot','usability']:
 (ref/'implementation'/group).mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'implementation'/group/'random-scenario.json',ref/'implementation'/group/'random-scenario.json')
# Oracle helper writes to a predictable output path.
(ref/'deliverables/sme-evaluation-2026-11-02/evidence').mkdir(parents=True,exist_ok=True)
files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for base in ['src','ui/src','knowledge','contracts','tests','third_party','deploy','mcp'] for p in (ROOT/base).rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.suffix!='.pyc'}
for n in ['CMakeLists.txt','CMakePresets.json','package.json','package-lock.json','build/anubis']:
 files[n]=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
(E/'source-manifest.json').write_text(json.dumps({'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'working_copy':'Includes uncommitted changes. Per-file digests identify evaluated bytes.','files':files},indent=2))
(E/'environment.json').write_text(json.dumps({'platform':platform.platform(),'machine':platform.machine(),'python':platform.python_version(),'tools':{k:subprocess.check_output(v,text=True).splitlines()[0] for k,v in {'cmake':['cmake','--version'],'clang':['clang','--version'],'node':['node','--version'],'npm':['npm','--version']}.items()}},indent=2))
# Assert current GUI versus CLI planning equality and preserve a compact verdict.
gui=json.loads((E/'gui-manual-result.json').read_text());cli=json.loads((E/'manual-result.json').read_text());assert gui['planning']==cli['planning']
(E/'gui-cli-comparison.json').write_text(json.dumps({'same_planning_object':True,'scope':'Alder current GUI and normalized workload CLI','gui_plan_sha256':hashlib.sha256(json.dumps(gui['planning'],sort_keys=True).encode()).hexdigest()},indent=2))
print('Evidence and source snapshot assembled')
