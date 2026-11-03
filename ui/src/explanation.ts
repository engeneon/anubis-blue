type J=Record<string,any>;
const titles:J={outcome:'What the result means',compute:'GPUs and factory size',memory:'Memory and servers',storage:'Shared storage',networks:'Factory networks',next:'What to do next'};
export function explainButton(host:HTMLElement,api:(p:string,m?:string,b?:unknown)=>Promise<any>,resultId:string,projectionId=''){
 const trigger=document.createElement('button');trigger.type='button';trigger.textContent='Explain this to me';host.append(trigger);
 trigger.onclick=async()=>{
  const dialog=document.createElement('dialog');dialog.className='explanation-dialog';dialog.setAttribute('aria-label','Explain this to me');
  const add=(tag:string,text:string,parent:HTMLElement=dialog)=>{const e=document.createElement(tag);e.textContent=text;parent.append(e);return e;};
  add('h2','Explain this to me');add('p','A plain-language explanation of this saved calculation. It cannot change your inputs, GPU counts or design handoff.');
  const close=add('button','Close') as HTMLButtonElement;close.onclick=()=>dialog.close();document.body.append(dialog);dialog.onclose=()=>dialog.remove();dialog.showModal();
  const status=add('p','Loading saved explanations…');status.setAttribute('role','status');status.setAttribute('aria-live','polite');const controls=add('section','');const content=add('section','');
  let stopped=false;dialog.addEventListener('close',()=>stopped=true);
  const show=(record:J)=>{content.replaceChildren();const d=record.data;add('p',d.mode==='model_assisted'?'Copilot explanation. Quantities come from the saved calculation. Qualitative prose remains model interpretation.':'Deterministic explanation. No model interpretation was used.',content);if(d.fallback_reason)add('p',d.fallback_reason,content);
   add('p',`Saved calculation ${d.packet.result_id}. ${d.packet.projection_id?'Saved projection '+d.packet.projection_id+'. ':''}Created ${new Date(d.created_at*1000).toLocaleString()}. ${d.model?'Model '+d.model+'.':''}`,content);
   for(const s of d.sections){add('h3',titles[s.id]||s.id,content);add('p',s.text,content);}
   add('p','To change demand or assumptions, refine the workload and calculate again. This explanation describes only the saved result identified above.',content);
   const sources=add('details','',content);add('summary','Source fields and assumptions',sources);add('pre',JSON.stringify({source_paths:d.packet.source_paths,reference_assumptions:d.packet.reference_assumptions,planning_policy:d.packet.planning_policy,result_digest:d.packet.result_digest},null,2),sources);
   const download=add('button','Download explanation',content) as HTMLButtonElement;download.onclick=()=>{const text='ANUBIS RESULT EXPLANATION\n\n'+d.sections.map((s:J)=>titles[s.id]+'\n'+s.text).join('\n\n')+'\n\nResult: '+d.packet.result_id+'\nMode: '+d.mode+'\nModel: '+(d.model||'none')+'\nCreated: '+new Date(d.created_at*1000).toISOString()+'\n';const url=URL.createObjectURL(new Blob([text],{type:'text/plain'}));const a=document.createElement('a');a.href=url;a.download='anubis-result-explanation.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  };
  try{
   const [profiles,history]=await Promise.all([api('copilot-profiles'),api('copilot-explanations/'+resultId+'/history')]);if(stopped)return;status.textContent='Select a connection, or use the deterministic explanation without an LLM.';
   const label=add('label','Explanation connection',controls);const select=document.createElement('select');select.setAttribute('aria-label','Explanation connection');const opt=document.createElement('option');opt.value='';opt.textContent='Deterministic explanation — no model';select.append(opt);
   for(const p of profiles.filter((p:J)=>p.data.enabled&&p.data.health==='capability_passed'&&(p.data.provider!=='mcp'||p.data.model_tool))){const o=document.createElement('option');o.value=p.id;o.textContent=p.data.name;select.append(o);}label.append(select);
   const publicLabel=add('label','',controls);const pub=document.createElement('input');pub.type='checkbox';publicLabel.append(pub,document.createTextNode('This saved result is public or fictional and may be sent to the selected provider'));add('p','Leave unchecked for customer or corporate data. Only connections approved for corporate data can then be used.',controls);
   const generate=add('button','Generate explanation',controls) as HTMLButtonElement;
   generate.onclick=async()=>{generate.disabled=true;select.disabled=true;status.className='explanation-busy';dialog.setAttribute('aria-busy','true');status.textContent='Preparing your explanation. The saved calculation remains unchanged…';try{
    let r=await api('copilot-explanations','POST',{result_id:resultId,projection_id:projectionId,profile_id:select.value,classification:pub.checked?'public':'corporate'});
    if(r.type==='job'){let done=false;for(let i=0;i<360&&!stopped;i++){await new Promise(resolve=>setTimeout(resolve,1000));const j=await api('jobs/'+r.id);status.textContent=`Copilot is ${j.data.state}. Your result remains unchanged…`;if(j.data.state==='succeeded'){r=await api('copilot-explanations/'+j.data.explanation_id);done=true;break;}if(['failed','cancelled','cancel_requested'].includes(j.data.state))throw Error(j.data.error?.message||'Explanation stopped. Use the deterministic option.');}if(stopped)return;if(!done)throw Error('Still preparing. Close and reopen this panel later to retrieve the saved explanation.');}
    if(!stopped){show(r);status.textContent='Explanation saved with this calculation.';}
   }catch(e){status.textContent=(e as Error).message;}finally{generate.disabled=false;select.disabled=false;status.className='';dialog.removeAttribute('aria-busy');}};
   if(history.length){const list=add('details','',controls);add('summary','Previously saved explanations',list);for(const r of history){const b=add('button',`${r.data.mode} · ${new Date(r.data.created_at*1000).toLocaleString()}`,list);b.onclick=()=>show(r);}show(history[0]);}
  }catch(e){status.textContent=(e as Error).message;}
 };
}
