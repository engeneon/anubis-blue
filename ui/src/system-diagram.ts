type Component = Record<string, any>;
const escape = (v: unknown) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
export const searchPlacementLabel = (value: unknown): string => value === 'external' ? 'Outside this AI Factory' : value === 'local' ? 'Inside this AI Factory' : value === 'none' ? 'No search or indexing' : 'Service location to confirm';
// This pure renderer is shared by the live interface and the customer playbook.
export function systemDiagram(c: Component, index = 0): string {
 const id = `arrow-${index}`, p=c.pattern, training=['training','adaptation'].includes(p), batch=['batch','generation'].includes(p), other=p==='other';
 const search=['retrieval','agent'].includes(p) && c.retrieval!=='none';
 const external=c.location==='external', unknown=c.location==='unknown';
 const node=(x:number,y:number,w:number,title:string,sub:string,fill='#ffffff')=>`<rect x="${x}" y="${y}" width="${w}" height="70" rx="10" fill="${fill}" stroke="#567585" stroke-width="1.5"/><text x="${x+w/2}" y="${y+27}" text-anchor="middle" class="label">${escape(title)}</text><text x="${x+w/2}" y="${y+49}" text-anchor="middle" class="sub">${escape(sub)}</text>`;
 const arrow=(d:string,dashed=false)=>`<path d="${d}" fill="none" stroke="#365e73" stroke-width="2" ${dashed?'stroke-dasharray="6 5"':''} marker-end="url(#${id})"/>`;
 const mark=(x:number,y:number,n:number)=>`<circle cx="${x}" cy="${y}" r="14" fill="#9a4e14"/><text x="${x}" y="${y+5}" text-anchor="middle" style="fill:white" font-size="15" font-weight="700">${n}</text>`;
 const rate=c.demand_mode==='users'?`${c.users||'?'} users / ${c.interval||'?'} seconds`:c.rate?`${c.rate} requests/min`:'Requests/min: to confirm';
 const input=training?'Training dataset':other?'Simulation inputs':batch?'Queued work':'Customers / channels';
 const entry=training?'Dataset preparation':other?'Simulation controller':batch?'Job scheduler':'Customer application';
 const worker=training?(p==='adaptation'?'Adaptation job':'Training job'):other?'GPU solver':p==='stream'?'Stream processing':p==='generation'?'Media generation':'Model serving';
 const model=c.model||'Model to confirm';
 const output=training?'Model checkpoints':other?'Simulation results':batch?'Completed outputs':p==='stream'?'Detected events':'Classification / answer';
 const reference=c.sizing_method==='reference';
 const demand=reference?`${c.reference_demand||'?'} ${c.reference_unit||'units'}/s`:training?`${c.tokens||'?'} tokens / ${c.days||'?'} days`:batch?`${c.jobs||'?'} jobs / ${c.window||'?'} hours`:other?'Mesh, steps and deadline':rate;
 const sub=reference?`${c.reference_gpus||'?'} GPUs per independent group`:other?'Solver-specific measurements':['stream','generation','adaptation'].includes(p)?'Specialist model and capacity to confirm':training?model:`${model} · ${c.calls||(p==='agent'?'?':'1')} calls/item`;
 const measure2=reference?`${c.reference_memory||'?'} GB/GPU. Capacity per hardware required`:training?'Tokens and completion deadline':other?'Throughput and peak GPU memory':p==='stream'||p==='generation'?'Work-item size and throughput':`${c.input_tokens||'2,000 preset'} input / ${c.output_tokens||'500 preset'} output tokens`;
 const scope=external?'COMPUTE OUTSIDE THIS AI FACTORY':unknown?'COMPUTE LOCATION — to confirm':'AI FACTORY COMPUTE — included in local sizing';
 const related=index>0?`Relationship to previous activity: ${c.relationship||'independent'}`:'Application activity';
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 520" role="img" aria-labelledby="diagram-title-${index} diagram-desc-${index}"><title id="diagram-title-${index}">${escape(c.name||'Application')} system architecture</title><desc id="diagram-desc-${index}">Inputs flow through the customer application to ${escape(worker)} and back to the customer application as results. The compute boundary and optional data dependencies are shown. Numbered markers identify demand, model work and retained data measurements. This is a conceptual application view, not a physical rack design.</desc><defs><marker id="${id}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#365e73"/></marker></defs><style>text{font-family:Arial,sans-serif;fill:#183543}.label{font-size:17px;font-weight:700}.sub{font-size:13px}.caption{font-size:14px}.boundary{font-size:13px;font-weight:700;letter-spacing:.5px}</style>
 <rect width="1000" height="520" rx="12" fill="#f7fafc"/>
 <text x="24" y="32" class="label">${escape(c.name||'Application component')}</text><text x="24" y="55" class="sub">${escape(related)} · conceptual system view</text>
 <rect x="20" y="85" width="480" height="272" rx="12" fill="#edf3f6" stroke="#b0c2cc"/><text x="36" y="110" class="boundary">CUSTOMER APPLICATION AND CHANNELS</text>
 <rect x="530" y="85" width="450" height="190" rx="12" fill="${external?'#f4eef9':'#e8f4f0'}" stroke="#598b7a" stroke-dasharray="8 5"/><text x="546" y="110" class="boundary">${escape(scope)}</text>
 ${node(40,155,185,input,training?'Measured training corpus':other?'Problem definition':batch?'Items awaiting processing':'Incoming work')}
 ${node(275,155,200,entry,demand)}
 ${node(580,155,330,worker,sub,'#ffffff')}
 ${arrow('M225 190 H275')}${arrow('M475 190 H580')}${mark(250,140,1)}${mark(558,140,2)}
 ${arrow('M745 225 V260 H375 V225')}<text x="515" y="252" class="caption">${escape(output)}</text>
 ${search?`${node(580,285,330,p==='agent'?'Tools / search service':'Search / document index',searchPlacementLabel(c.retrieval))}${c.retrieval==='external'?'<text x="745" y="350" text-anchor="middle" style="font-size:11px">e.g. customer search cluster or cloud search</text>':''}${arrow('M935 190 H955 V320 H910',true)}`:`<text x="550" y="310" class="caption">${p==='direct'?'No retrieval or tool branch in this pattern.':'Dependencies require confirmation with the customer.'}</text>`}
 ${node(275,290,200,'Retained data',c.storage_tb?`${c.storage_tb} TB locally retained`:'Capacity: unspecified','#fff8ea')}${arrow('M305 225 V290',true)}${mark(250,320,3)}
 <text x="24" y="386" class="sub">Solid arrows: main work and returned results. Dashed arrow: optional retention or dependency. Confirm implementation.</text>
 <rect x="20" y="404" width="960" height="96" rx="8" fill="white" stroke="#ccdbe2"/>
 ${mark(45,431,1)}<text x="67" y="435" class="caption">Demand at the application entry</text><text x="67" y="462" class="sub">${escape(demand)}</text>
 ${mark(365,431,2)}<text x="387" y="435" class="caption">Work at the compute service</text><text x="387" y="462" class="sub">${escape(measure2)}</text>
 ${mark(700,431,3)}<text x="722" y="435" class="caption">Data retained in this factory</text><text x="722" y="462" class="sub">Capacity, growth and retention period</text>
 </svg>`;
}
