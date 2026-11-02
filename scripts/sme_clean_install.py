import pathlib,tempfile,shutil,subprocess,json,datetime,os,time,urllib.request
root=pathlib.Path(__file__).resolve().parents[1]
out=root/'deliverables/sme-evaluation-2026-11-02/evidence'
target=pathlib.Path(tempfile.mkdtemp(prefix='anubis-clean-install-'))
for name in ['docs','src','third_party','tests','ui','knowledge','contracts','deploy','scripts','mcp','CMakeLists.txt','CMakePresets.json','package.json','package-lock.json']:
 p=root/name
 if p.is_dir():shutil.copytree(p,target/name,ignore=shutil.ignore_patterns('dist','__pycache__'))
 else:shutil.copy2(p,target/name)
checks=[]
for name,argv in [('configure',['cmake','--preset','local']),('compile',['cmake','--build','--preset','local','-j4']),('npm-install',['npm','ci','--ignore-scripts']),('ui',['npm','run','build']),('core',['ctest','--test-dir','build','--output-on-failure'])]:
 r=subprocess.run(argv,cwd=target,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/('install-'+name+'.log')).write_text(r.stdout.replace(str(target),'CLEAN_INSTALL_ROOT'));checks.append({'name':name,'argv':argv,'returncode':r.returncode})
 if r.returncode:break
if all(c['returncode']==0 for c in checks):
 p=subprocess.Popen(['python3','deploy/local/run.py','--port','8802'],cwd=target,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for _ in range(100):
   try:
    with urllib.request.urlopen('http://127.0.0.1:8802/health') as response:health=response.status
    break
   except Exception:time.sleep(.1)
  identity=target/'.anubis/identities.json';checks.append({'name':'launcher-first-login','health':health,'private_identity_mode':oct(identity.stat().st_mode&0o777),'nonempty_token':bool(json.loads(identity.read_text())[0]['token']),'returncode':0})
 finally:p.terminate();p.wait(timeout=10)
report={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Fresh directory and dependency installation on existing macOS toolchain. Not a clean operating system or cross-platform qualification.','checks':checks,'passed':len(checks)==6 and all(c['returncode']==0 for c in checks)}
(out/'clean-install.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));shutil.rmtree(target)
