"""Independent arithmetic checks plus deterministic replay for SME review."""
import pathlib,sys,json,hashlib,subprocess,copy
from fractions import Fraction as F
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
from test_usability import transform,compile_w
OUT=ROOT/'deliverables/sme-evaluation-2026-11-02/evidence';OUT.mkdir(parents=True,exist_ok=True)
b={'name':'Alder Contact Services SME','tenancy':'single','overlap':'yes','accepted':True,'components':[{'name':'Message classification','pattern':'direct','location':'local','model':'dense8b','rate':'100','calls':'1','input_tokens':'2000','output_tokens':'500','service_seconds':'5','storage_tb':'2','growth_gb_day':'10','horizon_days':'365'}],'network':{'initial_tb':'2','load_hours':'8','daily_ingest_gb':'10','daily_egress_gb':'1','utilization':'0.7','latency_ms':'20','storage_read_gbps':'4','storage_write_gbps':'2','overlap':'yes'}}
w=transform(b);r=compile_w(w);p=r['planning'];s=p['stage_calculations'][0];checks=[]
def check(name,actual,expected,tol=F(0)):
 passed=abs(F(str(actual))-expected)<=tol;checks.append({'name':name,'actual':str(actual),'expected_exact':str(expected),'tolerance':str(tol),'passed':passed});assert passed,(name,actual,expected)
check('business calls per second',s['demand'],F(100,60),F(1,10**6))
kv=F(2*32*8*128*2*8192*32,10**9);check('per GPU memory GB',s['required_GB_per_gpu'],16+kv+8,F(1,10**6))
hw=p['hardware'];a=p['policy']
# Derive capacity independently from the frozen hardware constants, not displayed capacity.
params=F(8*10**9);compute=F(hw['dense_bf16_TFLOPS'])*F(a['compute_efficiency'])*10**12/(2*params*2500) if 'dense_bf16_TFLOPS' in hw else None
for row in p['hardware_comparison']:
 h=row['hardware'];cap=min(F(h['dense_bf16_TFLOPS'])*F(a['compute_efficiency'])*10**12/(2*params*2500),F(h['bandwidth_TBps'])*1000*F(a['memory_efficiency'])/((F(16)+kv)/32*500))
 replicas=-(-F(100,60)//cap);gpus=8*((replicas+7)//8)
 check(row['platform']+' independent GPU count',row['raw_gpus'],F(gpus))
check('smallest eligible profile anchor',p['initial_gpus'],F(min(x['gpus'] for x in p['architecture']['anchors'] if x['gpus']>=p['raw_gpus'])))
check('retained usable bytes',p['storage'][0]['usable_bytes'],F(2*10**12+10*10**9*365)*F(5,4))
n=p['networks'];check('initial link Gbps',n['external_customer_datacenter']['initial_load_link_Gbps'],F(2*8000,8*3600)*F(12,10)/F(7,10),F(1,10**6))
check('storage read link Gbps',n['storage']['read_link_lower_bound_Gbps'],F(4)*F(12,10)/F(7,10),F(1,10**6))
check('storage write link Gbps',n['storage']['write_link_lower_bound_Gbps'],F(2)*F(12,10)/F(7,10),F(1,10**6))
assert r==compile_w(w)
checks.append({'name':'full CLI semantic result identical on repeat','passed':True})
unknown=copy.deepcopy(b);unknown['components'][0]['rate']='';u=compile_w(transform(unknown));assert u['candidates']==[]
checks.append({'name':'missing demand produces no candidate','passed':True})
for name,data in [('manual-intake',b),('manual-workload',w),('manual-result',r),('arithmetic-checks',{'checks':checks,'passed':all(c['passed'] for c in checks)})]:(OUT/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'passed':True,'checks':len(checks),'hardware':hw,'raw':p['raw_gpus'],'comparisons':[(x['platform'],x['raw_gpus']) for x in p['hardware_comparison']]}))
