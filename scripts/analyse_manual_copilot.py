"""Compare full planning outputs, demand facts and handoff requirements."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'deliverables/manual-copilot-comparison-2026-11-03'
def read(n):return json.loads((R/n).read_text())
def diff(a,b,path=''):
 if isinstance(a,dict) and isinstance(b,dict):
  out=[]
  for k in sorted(a.keys()|b.keys()):
   if k not in a or k not in b:out.append({'path':path+'/'+k,'manual':a.get(k),'assisted':b.get(k),'kind':'missing key'})
   else:out.extend(diff(a[k],b[k],path+'/'+k))
  return out
 if isinstance(a,list) and isinstance(b,list):
  if len(a)!=len(b):return [{'path':path,'manual':a,'assisted':b,'kind':'list length'}]
  return [x for i,(u,v) in enumerate(zip(a,b)) for x in diff(u,v,path+'/'+str(i))]
 return [] if a==b else [{'path':path,'manual':a,'assisted':b,'kind':'value'}]
a,b=read('manual-result.json'),read('assisted-result.json');pa,pb=a['planning'],b['planning'];ia,ib=read('manual-intake.json'),read('assisted-intake.json')
report={'scenario':read('execution-retry.json'),'initial_attempt':read('execution.json'),'planning_differences':diff(pa,pb),'handoff_requirement_differences':diff(ia['requirements'],ib['requirements']),'input_differences':diff(a['guided_context']['characterization']['guided_input'],b['guided_context']['characterization']['guided_input']),'fact_differences':diff(a['facts'],b['facts']),'whole_result_differences':diff(a,b),'metrics':[]}
for label,key in [('Workload GPUs','raw_gpus'),('Factory deployment GPUs','initial_gpus'),('Required GPU memory GB','required_GB_per_gpu'),('Workload host RAM GB','host_ram_GB_required'),('Workload local disk GB','local_disk_GB_required'),('CPU cores','cpu_cores_provision'),('Shared storage tiers','storage'),('Networks','networks')]:report['metrics'].append({'metric':label,'manual':pa.get(key),'assisted':pb.get(key),'equal':pa.get(key)==pb.get(key)})
report['full_planning_equal']=not report['planning_differences'];report['handoff_requirements_equal']=not report['handoff_requirement_differences']
(R/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['full_planning_equal','handoff_requirements_equal','planning_differences','input_differences','fact_differences']},indent=2))
