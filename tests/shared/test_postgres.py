"""PostgreSQL/SQLite semantic parity and concurrent API ownership tests."""
import concurrent.futures,json,os,pathlib,socket,subprocess,tempfile,time,urllib.request,urllib.error
ROOT=pathlib.Path('/app');token='isolated-shared-test-'+('x'*32);processes=[]
def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def api(base,path,body=None,method=None,extra=None):
 req=urllib.request.Request(base+'/api/v1/'+path,data=None if body is None else json.dumps(body).encode(),method=method,headers={'Content-Type':'application/json','Authorization':'Bearer '+token,**(extra or {})})
 try:
  with urllib.request.urlopen(req,timeout=30) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:
  with e:return e.code,json.load(e)
with tempfile.TemporaryDirectory() as tmp:
 try:
  urls=[]
  for i in range(3):
   selected=port();env={**os.environ,'ANUBIS_TOKEN':token}
   if i<2:env['ANUBIS_DATABASE_URL']=os.environ['ANUBIS_TEST_POSTGRES_URL']
   else:env.pop('ANUBIS_DATABASE_URL',None)
   proc=subprocess.Popen([str(ROOT/'build/anubis'),'--root',str(ROOT),'--db',f'{tmp}/worker{i}/db.sqlite','--port',str(selected)],env=env,stdout=subprocess.DEVNULL)
   processes.append(proc);base=f'http://127.0.0.1:{selected}';urls.append(base)
   for _ in range(100):
    try:
     if api(base,'capabilities')[0]==200:break
    except OSError:pass
    if proc.poll() is not None:raise RuntimeError('Service failed')
    time.sleep(.1)
   else:raise RuntimeError('Startup timed out')
  def run(base):
   _,case=api(base,'cases',{'name':'Repository parity'})
   _,draft=api(base,'cases/'+case['id']+'/drafts',json.loads((ROOT/'tests/fixtures/aster.json').read_text()))
   _,revision=api(base,'drafts/'+draft['id']+'/freeze',{},extra={'If-Match':'1'})
   _,job=api(base,'compilations',{'revision_id':revision['id']})
   for _ in range(100):
    _,current=api(base,'jobs/'+job['id'])
    if current['data']['state']=='succeeded':return case,draft,api(base,'results/'+current['data']['result_id'])[1]['data']['result']
    time.sleep(.1)
   raise RuntimeError(str(current))
  case,draft,pg=run(urls[0]);_,_,local=run(urls[2]);assert pg==local,'Repository changes semantic result'
  assert api(urls[1],'cases/'+case['id'])[0]==200,'Shared records unavailable to second API process'
  def update(base):return api(base,'drafts/'+draft['id'],draft['data'],'PATCH',{'If-Match':'1'})[0]
  with concurrent.futures.ThreadPoolExecutor() as pool:statuses=list(pool.map(update,urls[:2]))
  assert sorted(statuses)==[200,409],statuses
  def retry(base):return api(base,'cases',{'name':'Idempotency concurrency'},extra={'Idempotency-Key':'cross-process-key'})
  with concurrent.futures.ThreadPoolExecutor() as pool:replies=list(pool.map(retry,urls[:2]))
  assert [r[0] for r in replies]==[201,201],replies
  assert replies[0][1]['id']==replies[1][1]['id'],'Duplicate mutation across workers'
  print(json.dumps({'passed':True,'postgres_sqlite_semantic_parity':True,'cross_process_optimistic_conflict':True,'cross_process_idempotency':True,'production_qualified':False}))
 finally:
  for proc in processes:proc.terminate()
  for proc in processes:proc.wait(timeout=10)
