#!/usr/bin/env python3
"""Freeze primary benchmark methodology sources. Does not activate performance claims."""
import datetime,hashlib,json,pathlib,urllib.request
root=pathlib.Path(__file__).resolve().parents[1];dest=root/'knowledge/public-evidence';dest.mkdir(exist_ok=True)
headers={'User-Agent':'Anubis-evidence-source-capture/0.1','Accept':'application/vnd.github+json'}
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as r:return r.read()
records=[]
for repo,path,name in [('mlcommons/inference','Submission_Guidelines.md','mlperf-submission-guidelines'),('NVIDIA/TensorRT-LLM','docs/source/legacy/performance/perf-benchmarking.md','tensorrt-llm-benchmarking')]:
 try:
  from urllib.parse import quote
  commits=json.loads(get(f'https://api.github.com/repos/{repo}/commits?path={quote(path)}&per_page=1'))
  if not commits:raise RuntimeError('No source commit found')
  commit=commits[0]['sha'];url=f'https://raw.githubusercontent.com/{repo}/{commit}/{path}';content=get(url)
  file=dest/'sources'/f'{name}.md';file.write_bytes(content)
  records.append({'id':name,'repository':repo,'commit':commit,'url':url,'path':str(file.relative_to(root)),'sha256':hashlib.sha256(content).hexdigest(),'classification':'benchmark_methodology','activation':'not_performance_evidence','rights_status':'review_before_redistribution','captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 except Exception as e:records.append({'id':name,'status':'capture_failed','error':str(e),'activation':'none'})
(dest/'source-manifest.json').write_text(json.dumps({'strategy':'hybrid-public-first','records':records,'performance_qualification':False},indent=2)+'\n')
print(json.dumps([{'id':x['id'],'status':x.get('status','captured'),'commit':x.get('commit')} for x in records],indent=2))
