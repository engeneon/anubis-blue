#!/usr/bin/env python3
"""Run a named local Neon binary in an isolated runtime and record actual API observations.
Does not modify Neon sources or qualify GPU performance or production deployment.
"""
import argparse,hashlib,json,os,pathlib,socket,subprocess,tempfile,time,urllib.request,urllib.error
p=argparse.ArgumentParser();p.add_argument('--neon-root',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
binary=a.neon_root/'build/aifactorycad-reference-ui-server'
report={'target_binary':str(binary),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'source_commit':subprocess.check_output(['git','-C',str(a.neon_root),'rev-parse','HEAD'],text=True).strip(),'profile':'isolated-local-development','production_qualified':False,'tests':[]}
with tempfile.TemporaryDirectory() as temp:
 sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
 with open(pathlib.Path(temp)/'server.log','w+') as log:
  proc=subprocess.Popen([str(binary),str(port)],cwd=temp,env={**os.environ,'AIFACTORYCAD_RUNTIME_ROOT':temp+'/runtime','AIFACTORYCAD_API_PROFILE':'development_unsecured','AIFACTORYCAD_SECURITY_CONFIG':str(a.neon_root/'config/local_api_security.json')},stdout=log,stderr=log)
  def req(path,body=None):
   request=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
   try:
    with urllib.request.urlopen(request,timeout=45) as response:return response.status,json.load(response)
   except urllib.error.HTTPError as e:
    with e:return e.code,json.load(e)
  try:
   for _ in range(100):
    try:
     status,cap=req('/api/v1/capabilities');break
    except OSError:
     if proc.poll() is not None:raise RuntimeError('Neon process exited')
     time.sleep(.1)
   else:raise RuntimeError('Neon did not become ready')
   report['capabilities']=cap;report['tests'].append({'name':'capabilities','status':status,'pass':status==200 and cap.get('api_version')=='1.1.0'})
   for platform in ['HGX_B300','GB300_NVL72']:
    payload={'project':{'name':'Anubis isolated compatibility probe'},'requirements':{'platform':platform,'target_gpu_count':56,'network_fabric':'InfiniBand','east_west_fabric':'InfiniBand'}}
    status,result=req('/api/v1/compiler-runs/reference-architecture',payload)
    report['tests'].append({'name':platform,'http_status':status,'pass':status==200 and result.get('execution',{}).get('status')=='success' and result.get('selected_architecture',{}).get('platform')==platform,'payload':payload,'response_keys':sorted(result),'response_sha256':hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'result':{k:result.get(k) for k in ['status','result_status','execution','selected_architecture','architecture_readiness','governance','diagnostics']},'returned_scale':result.get('architecture_model',{}).get('scale')})
   report['passed']=all(t['pass'] for t in report['tests'])
  except Exception as e:
   log.flush();log.seek(0);report['error']=str(e);report['server_log']=log.read()[-3000:];report['passed']=False
  finally:proc.terminate();proc.wait(timeout=10)
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['profile','passed','production_qualified']}))
raise SystemExit(0 if report['passed'] else 1)
