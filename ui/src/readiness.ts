// Render server-owned minimum-input checks in manual and assisted intake.
type J=Record<string,any>;
export function readinessPanel(host:HTMLElement,report:J,fix?:(issue:J)=>void){
 host.replaceChildren();host.className='gpu-readiness '+(report.ready?'ready':'blocked');host.setAttribute('aria-label','GPU estimate readiness');
 const h=document.createElement('h2');h.textContent=report.ready?'GPU estimate inputs are ready':'GPU estimate blocked — required information is missing';host.append(h);
 const p=document.createElement('p');p.textContent=report.meaning;host.append(p);
 if(!report.ready){const list=document.createElement('ul');for(const item of report.missing){const li=document.createElement('li');const b=document.createElement(fix?'button':'strong');b.textContent=(item.component>=0?'Activity '+(item.component+1)+' · ':'')+item.label;if(fix)b.addEventListener('click',()=>fix(item));li.append(b,document.createTextNode(' — '+item.reason));list.append(li);}host.append(list);}
 const note=document.createElement('p');note.className='note';note.textContent='Minimum for text serving: local model or accepted preset, peak request rate (or active users and interval), calls per request, and input/output tokens. Accepted presets may supply token and model assumptions. Batch needs job count and completion window. Training needs token count and deadline. Specialist workloads need a scoped reference capacity. Storage and network unknowns remain visible but do not silently become zero.';host.append(note);
}
