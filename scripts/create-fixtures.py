import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def q(v,u,state='estimated',source='fictional_customer_story'):
 return dict(state=state,value=str(v),unit=u,origin='customer',source=source,**({'accepted':True} if state=='assumed' else {}))
def stage(i,t,obs,**kw):return dict(id=i,name=i.replace('_',' ').title(),type=t,observations=obs,**kw)
def case(name,stages,scenarios=None,**kw):return dict(schema_version='1.0',name=name,stages=stages,edges=[],scenarios=scenarios or [dict(id='normal',name='Normal',multiplier='1',failed_nodes=0)],tenancy='single',**kw)
mer=case('Meridian Industrial Services',[
 stage('assistant','inference',dict(users=q(1200,'count'),interval=q(120,'s'),extra_calls=q('.25','ratio','assumed'),input_tokens={'state':'unknown','reason':'Prompt distribution not supplied'},output_tokens={'state':'unknown','reason':'Estimated 300–700 tokens is not a qualified distribution'}),model='unresolved',notes='Private RAG assistant; retrieval and tool workload measurements pending.'),
 stage('reports','batch',dict(jobs=q(30000,'count'),window=q(8,'hour')),notes='Report-to-model-call expansion remains unresolved; one call per report is not established.'),
 stage('documents','data',dict(bytes=q(8,'TB'),free_fraction={'state':'unknown','reason':'Reserve not agreed'}),storage_tier='object')
], [dict(id='day',name='Daytime assistant',active_stages=['assistant','documents'],multiplier='1',failed_nodes=0),dict(id='overnight',name='Overnight reports',active_stages=['reports','documents'],multiplier='1',failed_nodes=0)])
har=case('Harbor Inference Cloud',[
 stage('standard','inference',dict(rate=q(40,'request/s'),input_tokens=q(2000,'token','assumed'),output_tokens=q(400,'token','assumed')),notes='8 tenants at 5 requests/s; endpoint routing unresolved'),
 stage('priority','inference',dict(rate=q(40,'request/s'),input_tokens=q(2000,'token','assumed'),output_tokens=q(400,'token','assumed')),notes='4 tenants at 10 requests/s; p95 TTFT 1s and ITL 50ms need boundaries'),
 stage('standard_burst','inference',dict(rate=q(120,'request/s'),input_tokens=q(2000,'token','assumed'),output_tokens=q(400,'token','assumed'))),
 stage('priority_reserved','inference',dict(rate=q(100,'request/s'),input_tokens=q(2000,'token','assumed'),output_tokens=q(400,'token','assumed')))
],[dict(id='normal',name='Normal traffic',active_stages=['standard','priority'],multiplier='1',failed_nodes=0),dict(id='simultaneous',name='Full simultaneous requested burst',active_stages=['standard_burst','priority_reserved'],multiplier='1',failed_nodes=0),dict(id='failure',name='Priority reservation after node loss',active_stages=['priority_reserved'],multiplier='1',failed_nodes=1)])
har['tenancy']='multi'
ast=case('Aster Language Research',[
 stage('campaign','training',dict(tokens=q(120000000000,'token'),window=q(30,'day'),effective_fraction=q('.85','ratio','assumed')),model='30B dense model exact revision unresolved'),
 stage('ingestion','transfer',dict(bytes=q(60,'TB'),window=q(12,'hour'))),
 stage('recovery','checkpoint',dict(checkpoint_bytes=q(2,'TiB','assumed'),save_window=q(120,'s'),recent=q(4,'count'),daily=q(30,'count')),storage_tier='file'),
 stage('corpus','data',dict(bytes=q(60,'TB')),storage_tier='object')
],[dict(id='campaign',name='Training and checkpoint stress',active_stages=['campaign','recovery','corpus'],multiplier='1',failed_nodes=0),dict(id='preload',name='Precampaign ingestion',active_stages=['ingestion','corpus'],multiplier='1',failed_nodes=0)])
fingerprint=dict(model='synthetic-dense-v1',runtime='synthetic-runtime-v1',precision='bf16',input_distribution='fixed-2000',output_distribution='fixed-400',slo='ttft-p95-1s-itl-p95-50ms',cache='cold',parallelism='TP4',quality='synthetic-only')
syn=case('Synthetic placement oracle',[
 stage('serving','inference',dict(rate=q(100,'request/s','known'),input_tokens=q(2000,'token','known'),output_tokens=q(400,'token','known')),fingerprint=fingerprint,platforms=['B200_TEST_ONLY'])
],[dict(id='node_loss',name='One-node loss',failed_nodes=1,multiplier='1')])
pack=dict(schema_version='1.0',id='synthetic-placement',version='1.0',channel='synthetic',dependencies=[],license='Test fixture authored for Anubis',description='Fictional performance. Never production evidence.',profiles=[dict(id='oracle-replica',platform='B200_TEST_ONLY',kind='inference',fingerprint=fingerprint,gpu_per_node=8,gpu_per_replica=4,capacity='12',admission='0.8',memory_required_bytes='60000000000',hbm_bytes='80000000000',host_ram_bytes='1000000000000',local_disk_bytes='8000000000000',cpu_cores=128,read_Bps='100000000000',write_Bps='100000000000',network_Bps='100000000000',source='framework-synthetic-example',evidence_basis='synthetic',scope='Exact synthetic fixture; all capacities fictional')])
for name,w in [('meridian',mer),('harbor',har),('aster',ast),('synthetic',syn)]:
 (root/f'tests/fixtures/{name}.json').write_text(json.dumps(w,indent=2)+'\n')
(root/'knowledge/synthetic.json').write_text(json.dumps(pack,indent=2)+'\n')
