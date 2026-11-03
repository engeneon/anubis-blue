import {readinessPanel} from './readiness.js';
import { systemDiagram, searchPlacementLabel } from './system-diagram.js';
type J=Record<string,any>;
const el=(tag:string,text='',cls='')=>{const x=document.createElement(tag);x.textContent=text;x.className=cls;return x;};
const button=(label:string,fn:()=>void|Promise<void>)=>{const b=el('button',label) as HTMLButtonElement;b.type='button';b.onclick=async()=>{b.disabled=true;try{await fn();}finally{b.disabled=false;}};return b;};
export function architectureView(host:HTMLElement,components:J[],select?:(i:number)=>void,current=-1){
 const box=el('section','','application-map');box.setAttribute('aria-label','Your application architecture');box.append(el('h2','Your application architecture'),el('p','Use this map to locate the application, its compute boundary and the measurements needed for sizing. Select an activity to describe its scale. Activity order and operating overlap are separate choices.'));
 const flow=el('div','','component-map');
 components.forEach((c,i)=>{const node=el('article','',i===current?'map-node selected':'map-node');node.append(select?button(c.name||'Application component',()=>select(i)):el('h3',c.name));
 const pattern=c.pattern;const diagram=el('div','','system-diagram');diagram.tabIndex=0;diagram.setAttribute('aria-label','Scrollable system architecture diagram');diagram.innerHTML=systemDiagram(c,i);node.append(diagram,el('p',`Compute: ${c.location==='external'?'Outside this AI Factory (customer GPU cluster or cloud API)':c.location==='unknown'?'Location to confirm':'Inside this AI Factory'} · ${c.relationship||'independent'}`),el('p',c.support||(c.sizing_method==='reference'?'Reference capacity sizing':['stream','generation','adaptation','other'].includes(pattern)?'Specialist measurements required':'Analytical sizing')));
 if(['retrieval','agent'].includes(pattern))node.append(el('p',`Search and indexing service: ${searchPlacementLabel(c.retrieval)}.`));
 if(['retrieval','agent'].includes(pattern)&&c.retrieval==='external')node.append(el('p','Existing search service outside the AI Factory being sized. Examples include a customer datacenter search cluster or a managed cloud search service. Its source documents and index may use different storage systems. This choice does not identify a storage product or require public Internet access.'));
 node.append(el('small',c.sizing_method==='reference'?'Measure work units per second, capacity per complete GPU group and peak memory on each GPU':pattern==='other'?'Measure at solver: throughput, memory, mesh and deadline':pattern==='training'?'Measure dataset tokens and training deadline':pattern==='batch'?'Measure at queue: jobs and completion window':'Measure at entry: requests. At model: prompt and response size.'));
 flow.append(node);
 });box.append(flow);host.append(box);
}
export async function mountGuided(host:HTMLElement,api:(p:string,m?:string,b?:unknown)=>Promise<any>,complete:(w:J)=>Promise<void>,existing?:J,advanced?:()=>void,initialStep=0){
 const [catalog,planning]=await Promise.all([api('guided-catalog'),api('planning-catalog')]);if(!host.isConnected)return;
 let recovered:J|null=null;try{recovered=JSON.parse(sessionStorage.getItem('anubis-guided-draft')||'null');}catch{}
 const state:J=existing?structuredClone(existing):recovered||{name:'',tenancy:'single',overlap:'unknown',accepted:false,components:[],notes:''};
 state.network ||= {};
 if(initialStep===3)state.accepted=false;
 let step=initialStep,selected=0,error='',preview:J|null=null;
 let readinessHost:HTMLElement|null=null,calculateButton:HTMLButtonElement|null=null,readinessTicket=0,readinessTimer:ReturnType<typeof setTimeout>;
 const fixInput=(issue:J)=>{selected=Math.max(0,issue.component);step=issue.field==='architecture'?3:issue.component<0?0:['location','retrieval','name'].includes(issue.field)?1:2;draw();const selector='[data-input-key="'+issue.field+'"]';(host.querySelector<HTMLElement>(selector+'[data-component-index="'+issue.component+'"]')||host.querySelector<HTMLElement>(selector))?.focus();};
 async function updateReadiness(){const ticket=++readinessTicket;try{const report=await api('guided-readiness','POST',state);if(ticket!==readinessTicket||!host.isConnected)return;if(readinessHost)readinessPanel(readinessHost,report,fixInput);if(calculateButton)calculateButton.disabled=!report.ready;}catch{if(readinessHost)readinessHost.textContent='GPU readiness check unavailable. Resolve the connection before calculating.';if(calculateButton)calculateButton.disabled=true;}}
 function scheduleReadiness(){readinessTicket++;if(calculateButton)calculateButton.disabled=true;clearTimeout(readinessTimer);readinessTimer=setTimeout(()=>void updateReadiness(),180);}
 const persist=()=>{if(!existing)sessionStorage.setItem('anubis-guided-draft',JSON.stringify(state));};
 const names=['1 Choose application','2 Confirm arrangement','3 Describe scale','4 Review and estimate'];
 function manualEdit(target:J,key:string){
  if(!state.input_basis)return;
  const index=state.components.indexOf(target);
  const path=index>=0?'components.'+index+'.'+key:target===state.network?'network.'+key:key;
  state.input_basis[path]=null;
 }
 function removeComponent(index:number){
  if(state.input_basis){
   const next:J={};
   for(const [key,value] of Object.entries(state.input_basis)){
    const match=/^components\.(\d+)\.(.+)$/.exec(key);
    if(!match){next[key]=value;continue;}
    const old=Number(match[1]);
    if(old!==index)next['components.'+(old>index?old-1:old)+'.'+match[2]]=value;
   }
   state.input_basis=next;
  }
  state.components.splice(index,1);
 }
 function field(label:string,key:string,target:J,help:string,options?:[string,string][],fallback=''){
  const wrap=el('div','','field');const id='guided-'+crypto.randomUUID(),l=el('label',label);l.setAttribute('for',id);
  let control:HTMLInputElement|HTMLSelectElement;
  if(options){control=document.createElement('select');for(const [v,t]of options){const o=document.createElement('option');o.value=v;o.textContent=t;control.append(o);}control.value=target[key]??fallback;control.onchange=()=>{target[key]=control.value;manualEdit(target,key);preview=null;persist();draw();};}
  else {control=document.createElement('input');control.value=target[key]??'';control.placeholder=fallback?'Preset: '+fallback:'Not sure yet';control.oninput=()=>{target[key]=control.value;manualEdit(target,key);preview=null;persist();scheduleReadiness();};}
  control.dataset.inputKey=key;control.dataset.componentIndex=String(state.components.indexOf(target));control.id=id;const desc=el('p',help,'field-definition');desc.id=id+'-help';control.setAttribute('aria-describedby',desc.id);l.title=help;wrap.append(l,control,desc);return wrap;
 }
 function check(label:string,key:string,target:J,help:string){const wrap=el('div','','field'),l=el('label'),c=document.createElement('input');c.type='checkbox';c.checked=!!target[key];c.onchange=()=>{target[key]=c.checked;manualEdit(target,key);preview=null;persist();scheduleReadiness();};c.dataset.inputKey=key;c.dataset.componentIndex=String(state.components.indexOf(target));l.append(c,document.createTextNode(label));wrap.append(l,el('p',help,'field-definition'));return wrap;}
 function draw(){
  persist();host.replaceChildren();host.append(el('h1',existing?'Refine your application estimate':'New engagement'),el('p','Choose an application, describe its scale, then obtain GPU, memory, storage and network requirements for your downstream AI Factory design tool or process.'));
  const nav=el('nav','','steps');nav.setAttribute('aria-label','Guided sizing steps');names.forEach((name,i)=>{const b=button(name,()=>{step=i;error='';draw();});if(step===i)b.setAttribute('aria-current','step');nav.append(b);});host.append(nav);
  readinessHost=el('section');host.append(readinessHost);calculateButton=null;void updateReadiness();
  const alert=el('p',error,'warning');alert.setAttribute('role','alert');if(error)host.append(alert);
  if(state.components.length)architectureView(host,state.components,(i)=>{selected=i;step=2;draw();},step===2?selected:-1);
  if(step===0){host.append(field('Customer workload name','name',state,'Use the customer and application name. This name follows the estimate into the design handoff.'));
   const grid=el('div','','pattern-grid');for(const p of catalog.patterns){const card=el('section','','panel');card.append(el('h2',p.name),el('p',p.description),el('p',p.sizing),button('Add '+p.name,()=>{if(state.components.length>=16){error='Use at most 16 components.';draw();return;}state.components.push({name:p.name,pattern:p.id,location:'local',relationship:'independent',demand_mode:'rate',model:'dense8b',retrieval:'unknown'});selected=state.components.length-1;preview=null;persist();draw();}));grid.append(card);}host.append(grid,el('p','Combine patterns when the application performs distinct jobs. Do not add each software microservice. For simulation or an unmatched application, choose Other GPU application.'));
  }
  if(step===1){host.append(field('Factory users','tenancy',state,'Tenancy identifies organisations sharing the factory. it does not establish isolation feasibility.',[['single','One organisation'],['multi','Multiple tenants']]));
   host.append(field('Do activities run at the same time?','overlap',state,'Choose separate windows only when the schedule prevents overlap. Dependencies alone do not prevent concurrent tasks.',[['unknown','Not sure — estimate simultaneous demand'],['yes','Yes — overlapping demand'],['no','No — separate operating windows']]));
   state.components.forEach((c:J,i:number)=>{const box=el('section','','panel');box.append(el('h2',c.name),field('Component name '+(i+1),'name',c,'Use a business activity name, such as customer assistant or overnight summaries.'),field('Compute location '+(i+1),'location',c,'Compute outside this AI Factory could be an existing customer GPU cluster or a managed model API. Its GPUs are excluded from this factory count. Keep connectivity, local copies and supporting services in scope.',[['local','In this factory'],['external','Outside this AI Factory (customer cluster or cloud API)'],['unknown','Not sure yet']]));
    if(i>0)box.append(field('Relationship '+(i+1),'relationship',c,'Relationship to the previous component. After and conditional describe order, not capacity sharing.',[['independent','Independent'],['after','After previous component'],['alongside','Alongside previous component'],['conditional','Conditional on previous component']]));
    box.append(check('Reserve dedicated capacity '+(i+1),'dedicated',c,'When selected, component capacity is not reused between separate operating windows.'));
    if(['retrieval','agent'].includes(c.pattern))box.append(field('Search and indexing location '+(i+1),'retrieval',c,'Where do search, embeddings and index refresh run relative to this AI Factory? An outside service could be a customer datacenter search cluster or a managed cloud search platform. Record the service and document-storage system separately in the notes. Outside does not necessarily mean another site or public Internet. Local or uncertain placement remains a separate resource gap.',[['unknown','Not sure yet'],['external','Existing service outside this AI Factory'],['local','In this factory'],...(c.pattern==='agent'?[['none','No search or indexing'] as [string,string]]:[])]));
    box.append(button('Remove '+c.name,()=>{removeComponent(i);selected=0;preview=null;persist();draw();}));host.append(box);
   });
  }
  if(step===2){const c=state.components[selected];if(!c){host.append(el('p','Choose an application component first.'));}else{
   host.append(el('h2','Describe '+c.name));const specialist=['stream','generation','adaptation','other'].includes(c.pattern);
   if(c.location==='local')host.append(field('Sizing method','sizing_method',c,'Use analytical planning for supported dense text models. Reference capacity replicates complete independent groups from a matching benchmark or explicitly accepted planning assumption.',[['analytical','Analytical model'],['reference','Reference capacity for independent work']], 'analytical'));
   if(c.location==='local'&&c.sizing_method==='reference'){
    host.append(el('p','Reference sizing does not infer distributed scaling or performance on another GPU. Use the same work unit and model/configuration for demand and each capacity. Fictional examples are assumptions, never benchmark measurements.','scope-notice'));
    for(const [label,key,help] of [
     ['Work unit','reference_unit','Name a completed unit such as frame, image, training run or simulation.'],
     ['Peak work units per second','reference_demand','Aggregate independent work due per second. For a batch, divide the number of items by available seconds.'],
     ['GPUs per reference group','reference_gpus','Use 1, 2, 4, 8 or a multiple of 8 GPUs up to 1024 for one complete group. Its capacity is repeated, not extrapolated inside one distributed job.'],
     ['Required GPU memory in GB','reference_memory','Peak memory required on each GPU in the stated configuration.'],
     ['H200 work units per second per group','reference_h200','Capacity measured or explicitly assumed for this exact H200 group.'],
     ['B200 work units per second per group','reference_b200','Capacity measured or explicitly assumed for this exact B200 group.'],
     ['B300 work units per second per group','reference_b300','Capacity measured or explicitly assumed for this exact B300 group.'],
     ['Reference source and conditions','reference_source','Identify benchmark or planning assumption, model/solver version, precision, workload size, group size and scope.']])host.append(field(label,key,c,help));
    host.append(check('Independent reference groups can serve this demand','reference_independent',c,'Confirm that work can be dispatched to replicated complete groups. A single larger mesh or model is not independent work.'),check('Reference includes local search and indexing','reference_includes_support',c,'Required when local retrieval support belongs to this component. The reference must cover that full scope.'),check('I accept this reference capacity and its scope','reference_accepted',c,'An explicit consultant planning decision. Do not mark invented numbers as measured.'));
   } else
   if(specialist||c.location!=='local')host.append(el('p',c.location==='external'?'This component uses compute outside this AI Factory, such as a customer GPU cluster or managed inference endpoint. Describe any data retained locally below.':c.pattern==='other'?'Solver-specific measurements required: solver/version, mesh size, solver steps, GPU throughput, memory and completion deadline. Select Reference capacity above to size independent complete GPU groups. Without a scoped reference, a GPU estimate is blocked.':'Select Reference capacity above and enter the model/configuration, work rate, capacity per GPU group and memory. Without those inputs a GPU estimate is blocked.','scope-notice'));
   else {host.append(field('Model preset','model',c,'Choose the intended model or an explicit planning assumption. Model choice is not a guarantee of application quality.',Object.keys(planning.models).map(k=>[k,k+' · planning assumption'] as [string,string])));
    if(c.pattern==='training'){host.append(field('Training tokens','tokens',c,'Total tokens processed across repetitions. Obtain from the tokenised training dataset and epoch count.'),field('Training deadline in days','days',c,'Available calendar days. The preset assumes 85% useful training time. refine when measured.'));}
    else {if(c.pattern==='batch')host.append(field('Jobs per window','jobs',c,'Count queued items to complete, not simultaneous users.'),field('Completion window in hours','window',c,'Hours available between input readiness and the business deadline.'));
     else {host.append(field('Describe demand using','demand_mode',c,'Use one approach to avoid counting the same demand twice.',[['rate','Requests per minute'],['users','Active users and request interval']]));if(c.demand_mode==='users')host.append(field('Active users','users',c,'Users contributing traffic during a busy period. obtain from application logs.'),field('Seconds between requests per user','interval',c,'Average interval for each active user in the selected busy period. Obtain from request timestamps.'));else host.append(field('Peak requests per minute','rate',c,'Count application requests during a representative busy period. Divide busiest-hour requests by 60. Leave blank if unknown.'));}
     host.append(field('Model calls per request or job','calls',c,'Include retries and agent loops. Sample complete transaction traces. Agent call count has no automatic default.',undefined,c.pattern==='agent'?'':'1'),field('Input tokens per model call','input_tokens',c,'Include prompt, history and retrieved passages. Use serving logs or the model tokenizer. Blank uses the displayed preset.',undefined,'2000'),field('Output tokens per model call','output_tokens',c,'Average generated response size from serving logs or tokenised examples. Blank uses the displayed preset.',undefined,'500'));
     const extra=el('details');extra.append(el('summary','Optional service target'),field('Response target in seconds','service_seconds',c,'p95 complete model response target. Kept for validation. this analytical estimate does not certify latency.'));host.append(extra);
    }
   }
   const data=el('details');data.append(el('summary','Data capacity and growth'),field('Locally retained data in TB','storage_tb',c,'Logical data retained in this factory. Measure storage inventory. Blank means unspecified, not zero. avoid entering a shared corpus twice.'),field('Daily growth in GB','growth_gb_day',c,'Net daily retained growth. Measure inventory change. blank adds no growth assumption.'),field('Planning horizon in days','horizon_days',c,'Period over which growth is accumulated. Blank uses 365 days.',undefined,'365'));host.append(data);
   const network=el('details');network.append(el('summary','Factory networks and customer datacenter connection'),el('p','Enter these factory-wide values once. Initial data is loaded from the customer datacenter over an external connection. Storage uses a physically dedicated network. Converged storage networking is excluded.'));
   for(const [label,key,help,preset] of [
    ['Initial dataset to load in TB','initial_tb','Total data crossing from the customer datacenter into the factory. Use the actual transfer volume, not compressed storage capacity.',''],
    ['Initial loading window in hours','load_hours','Hours allowed to complete the initial transfer. Volume divided by this window determines the required average transfer rate.',''],
    ['Ongoing incoming data in GB per day','daily_ingest_gb','Additional bulk data beyond model request traffic. Enter zero when confirmed absent. Daily averages do not describe bursts.',''],
    ['Ongoing outgoing data in GB per day','daily_egress_gb','Additional bulk exports beyond model response traffic. Enter zero when confirmed absent.',''],
    ['Usable link fraction','utilization','Planning fraction of nominal link bandwidth available to payload and protocol traffic. 0.7 means 70%. This is an explicit assumption, not an industry guarantee.','0.7'],
    ['Customer datacenter round-trip target in ms','latency_ms','Required round-trip latency between the customer datacenter and the factory border. Obtain from the service owner and validate with network measurements.',''],
    ['Aggregate storage reads in Gbps','storage_read_gbps','Peak read payload across the dedicated storage fabric. Obtain from storage telemetry or dataset read volume and its read window. Do not infer it from storage capacity.',''],
    ['Aggregate storage writes in Gbps','storage_write_gbps','Peak write payload including initial loading, checkpoints and ingestion when concurrent. Enter zero only if no writes are required.',''],
    ['East-west payload per GPU in Gbps','ew_per_gpu_gbps','Optional measured collective-communication demand per GPU. The selected reference profile informs topology but does not qualify workload bandwidth.','']
   ])network.append(field(label,key,state.network,help,undefined,preset));
   network.append(field('Does initial loading overlap normal operation?','overlap',state.network,'Overlapping phases add ingress demand. Separate phases use the greater requirement.',[['yes','Yes — add the demands'],['no','No — use the greater demand']], 'yes'));host.append(network);
   host.append(field('Customer context and measurement notes','notes',state,'Record unknowns, measurements, source dates, external service dependencies and specialist workload requirements.'));
  }}
  if(step===3){host.append(el('h2','Review your first estimate'),el('p','The estimate uses your confirmed architecture and the assumptions below. The readiness check must pass for a complete GPU estimate. Incomplete assessments can be saved separately and are not complete sizing outcomes.'));
   host.append(field('Infrastructure deployment profile','architecture',state,'This selects factory deployment anchors, not application architecture. Workload GPU estimates remain separate.',planning.architectures.map((a:J)=>[a.id,`${a.platform.replace('HGX_','HGX ')} GPUs · ${a.fabric} network · ${a.family.replace('Enterprise RA dual plane','Enterprise reference design with two network planes')}`] as [string,string]),catalog.policy.architecture),field('Sensitivity envelope','sensitivity',state,'Explore faster/slower throughput. This is a sensitivity range, not a statistical confidence interval.',[['10','±10%'],['20','±20%'],['30','±30%']], '30'));
   const detail=el('details');detail.append(el('summary','Inspect versioned planning defaults'),el('p',`Profile ${catalog.version}. Defaults are planning assumptions. customer values override them.`),el('pre',JSON.stringify({serving:catalog.serving,policy:catalog.policy},null,2)));host.append(detail);
   host.append(el('p',`Network assumptions: physically dedicated storage fabric. Usable link fraction ${state.network.utilization||'0.7'}. Initial loading ${state.network.overlap==='no'?'does not overlap':'overlaps'} normal operation. Missing transfer and throughput measurements remain unresolved.`));
   host.append(check('Use these planning assumptions','accepted',state,'I have reviewed the model, token presets, efficiency and memory assumptions. Specialist and unknown demand are not converted to zero.'));
   host.append(button('Preview requirements',async()=>{try{preview=await api('guided-workloads','POST',state);error='';draw();}catch(e){error=(e as Error).message;draw();}}));
   if(preview){for(const q of preview.characterization.follow_up)host.append(el('p',q,'scope-notice'));host.append(el('p',`${preview.stages.length} resource components generated. Entered quantities are recorded as estimates. preset quantities retain their template origin.`));}
   calculateButton=button('Calculate estimate',async()=>{try{const ready=await api('guided-readiness','POST',state);if(!ready.ready){if(readinessHost)readinessPanel(readinessHost,ready,fixInput);throw Error('Complete the required GPU inputs listed above.');}if(!state.accepted)throw Error('Review and accept the planning assumptions first.');const w=await api('guided-workloads','POST',state);await complete(w);if(!existing)sessionStorage.removeItem("anubis-guided-draft");}catch(e){error=(e as Error).message;draw();}}) as HTMLButtonElement;calculateButton.disabled=true;host.append(calculateButton);
   host.append(button('Save incomplete assessment without a GPU estimate',async()=>{try{const w=await api('guided-workloads','POST',state);await complete(w);if(!existing)sessionStorage.removeItem('anubis-guided-draft');}catch(e){error=(e as Error).message;draw();}}));
  }
  const controls=el('div','','actions');if(step>0)controls.append(button('Previous',()=>{step--;error='';draw();}));if(step<3)controls.append(button('Continue',()=>{if(!state.name.trim()){error='Enter the customer workload name.';}else if(!state.components.length){error='Choose at least one application pattern.';}else {step++;error='';}draw();}));if(advanced)controls.append(button('Open advanced workload editor',advanced));if(!existing)controls.append(button('Clear unsaved intake',()=>{sessionStorage.removeItem('anubis-guided-draft');state.name='';state.components=[];state.notes='';state.accepted=false;step=0;selected=0;error='';draw();}));host.append(controls);
 }
 draw();
}
