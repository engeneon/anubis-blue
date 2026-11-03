"""Build the four GPU-complete Word playbooks from verified GUI captures."""
from pathlib import Path
import json,sys,shutil
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'deliverables/complete-playbooks';OUT=ROOT/'docs/playbooks';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'deliverables/usability'))
from playbook_typography import install_styles,render_inline
labels={'name':'Component name','pattern':'Application pattern','location':'Compute location','relationship':'Relationship','model':'Model preset','rate':'Peak requests per minute','calls':'Model calls per request or job','input_tokens':'Input tokens per model call','output_tokens':'Output tokens per model call','retrieval':'Search and indexing location','dedicated':'Reserve dedicated capacity','sizing_method':'Sizing method','reference_demand':'Peak work units per second','reference_unit':'Work unit','reference_gpus':'GPUs per reference group','reference_memory':'Required GPU memory in GB','reference_h200':'H200 work units per second per group','reference_b200':'B200 work units per second per group','reference_b300':'B300 work units per second per group','reference_source':'Reference source and conditions','reference_independent':'Independent reference groups can serve this demand','reference_accepted':'I accept this reference capacity and its scope'}
methods={
'name':('Business activity being sized. Numbered labels follow the order of components in the active route.','Agree a recognisable activity name with the application owner. Use the matching diagram to check its scope.'),
'pattern':('Application behaviour, not a server type.','Walk through a customer task. Identify text serving, retrieval, media processing or solver work.'),
'location':('Where computation runs relative to this factory.','Confirm the hosting owner and deployment boundary. Outside services do not contribute local model GPUs.'),
'relationship':('Order or relationship of activities. This is separate from whether demand overlaps.','Review the business flow with the application owner. Confirm scheduling separately.'),
'model':('Language-model size and architecture preset. It is not a quality guarantee.','Use the model registry or serving configuration. Record an explicitly accepted assumption when the model has not been selected.'),
'rate':('Busy-period application requests per minute.','Count application gateway requests by minute in a representative peak. Divide busiest-hour requests by sixty only when that average is an accepted planning basis.'),
'calls':('Model invocations per complete customer request, including retries.','Inspect distributed transaction traces or model gateway logs. Count calls across the entire request, including agent loops.'),
'input_tokens':('Prompt, history and retrieved passages sent to a model call.','Read prompt-token metrics from serving logs or tokenize representative full prompts with the exact model tokenizer.'),
'output_tokens':('Generated response tokens per model call.','Read completion-token metrics or tokenize representative outputs. Choose a planning distribution with the service owner.'),
'retrieval':('Location of search, embedding and indexing support.','Ask the search-platform owner where the index is built and queried. Do not infer its footprint from the source-corpus size.'),
'dedicated':('Whether this activity keeps capacity reserved rather than reusing a pool.','Agree isolation and reservation requirements with the service owner. Tenant count is not automatically a GPU multiplier.'),
'sizing_method':('Analytical text sizing or replication of a complete reference GPU group.','Use analytical sizing for supported language models. Select reference capacity for a scoped specialist workload.'),
'reference_unit':('Completed unit of work, such as a processed frame or complete simulation.','Define the exact work item, input dimensions, quality settings, precision and success condition with the application owner.'),
'reference_demand':('Aggregate independent work units due per second.','Count peak arriving work. For batch work divide items by available seconds. Camera demand can be cameras multiplied by sampled frames per second.'),
'reference_gpus':('GPUs in a complete independently repeatable group.','Read the tested or assumed deployment configuration. Use one, two, four, eight or a multiple of eight GPUs. Do not scale a single larger mesh by adding unrelated groups.'),
'reference_memory':('Peak memory required on each GPU in the reference configuration.','Measure the busiest device with GPU telemetry during representative work. Include weights, working state and buffers. Record the source and margin.'),
'reference_source':('Source and operating conditions for the capacity assumption.','Record benchmark or engineering-assumption provenance, date, model or solver version, precision, input dimensions, group size and scope. Fictional example values are not measurements.'),
'reference_independent':('Whether independent full groups can share the incoming work.','Check that the scheduler can route separate jobs or requests to each group. A single job requiring a larger distributed system does not satisfy this assumption.'),
'reference_accepted':('Consultant acceptance of reference scope and assumptions.','Review demand, capacity, memory and group independence together. Reaccept after Copilot refinement only if the reference remains applicable.')}
for k in ['reference_h200','reference_b200','reference_b300']:methods[k]=('Capacity per complete group on this specific GPU platform, in the same work units per second as demand.','Use a matching measured run or an explicit engineering assumption for this platform. Do not silently translate throughput measured on another GPU.')
for s in json.loads((ROOT/'tests/fixtures/architecture-scenarios.json').read_text()):
 if s['id'] not in ['S11','S13','S14','S16']:continue
 folder=DATA/s['id'];routes={m:json.loads((folder/(m+'.json')).read_text()) for m in ['manual','assisted']}
 for mode,r in routes.items():
  assert r.get('validated'),(s['id'],mode,'GUI run incomplete')
  result=json.loads((folder/(mode+'-result.json')).read_text());assert result['planning']['status']=='conditional' and result['candidates']
  assert {h['platform']:h['raw_gpus'] for h in result['planning']['hardware_comparison']}==s['expected_gpu_counts']
 filename=s['id']+'_'+s['name'].replace(' ','_')+'_Playbook.docx'
 reference=ROOT/'deliverables/blue-playbooks'/filename
 if not reference.exists():reference=OUT/filename
 d=Document(reference)
 for child in list(d._element.body):
  if child.tag!=qn('w:sectPr'):d._element.body.remove(child)
 sec=d.sections[0];sec.page_width=Inches(11.69);sec.page_height=Inches(8.27);sec.top_margin=sec.bottom_margin=Inches(.5);sec.left_margin=sec.right_margin=Inches(.5)
 d.core_properties.author='Traiano Giuseppe Welcome';d.core_properties.title='Anubis '+s['name']+' playbook';d.core_properties.comments='traiano@gmail.com'
 install_styles(d)
 for name in ['Normal','Title','Heading 1','Heading 2','Heading 3']:
  d.styles[name].font.name='Arial';d.styles[name].font.color.rgb=RGBColor(0,0,0)
 d.styles['Normal'].font.size=Pt(10);d.styles['Normal'].paragraph_format.space_after=Pt(5);d.styles['Title'].font.size=Pt(25)
 sec.header.paragraphs[0].text='ANUBIS  |  '+s['id']+'  |  WORKLOAD SIZING PLAYBOOK'
 sec.footer.paragraphs[0].text='Version 2.0  |  3 November 2026  |  Traiano Giuseppe Welcome  |  traiano@gmail.com'
 def para(text):p=d.add_paragraph();render_inline(p,text.replace(';','.'));return p
 def heading(title):d.add_heading(title,1)
 def page(title):
  h=d.add_heading(title,1);h.paragraph_format.page_break_before=True
 def table(headers,rows,widths):
  t=d.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.autofit=False
  for col,w in zip(t.columns,widths):col.width=Inches(w)
  for c,h,w in zip(t.rows[0].cells,headers,widths):c.width=Inches(w);render_inline(c.paragraphs[0],h)
  t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
  for row in rows:
   cells=t.add_row().cells
   for cell,text,w in zip(cells,row,widths):cell.width=Inches(w);render_inline(cell.paragraphs[0],str(text).replace(';','.'))
   cells[0]._tc.getparent().get_or_add_trPr().append(OxmlElement('w:cantSplit'))
  return t
 def pic(cell,path):
  im=Image.open(path);w,h=im.size;scale=min(6.05/w,4.5/h);cell.paragraphs[0].add_run().add_picture(str(path),width=Inches(w*scale),height=Inches(h*scale))
 d.add_heading('Anubis '+s['name']+' playbook',0)
 para('Follow the manual or Copilot-assisted route to calculate workload GPU requirements, prepare a design handoff, obtain a plain-language explanation and save the completed engagement.')
 para('Reader key. [[field:UI field]] identifies a screen label. [[value:Entered value]] is literal content. [[control:Button]] identifies an action. [[state:Checked]] and [[state:blank]] identify settings.')
 heading('Customer scenario')
 para(s['original_story']);para(s['planning_assumptions'])
 heading('Workflow input register')
 rows=[]
 def add(scope,field,value,basis,definition,method):rows.append({'id':'I'+str(len(rows)+1).zfill(2),'scope':scope,'field':field,'value':str(value),'basis':basis,'definition':definition,'method':method})
 add('Engagement','Customer workload name',s['name']+' manual playbook / '+s['name']+' assisted playbook','Entered','Identifies the two separate saved runs.','Choose the route suffix to avoid mixing results.')
 add('Engagement','Factory users','Multiple tenants' if s['planning_input']['tenancy']=='multi' else 'One organisation','Selected','Organisations sharing the factory.','Confirm commercial and organisational scope. Tenancy does not multiply aggregate demand automatically.')
 add('Engagement','Do activities run at the same time?','Yes — overlapping demand','Selected','Peak workloads may coincide.','Review schedules and telemetry with the operations owner.')
 for c in s['planning_input']['components']:
  for k,v in c.items():
   if c['location']=='external' and k in ['model','rate','calls','input_tokens','output_tokens','retrieval']:continue
   if k=='retrieval' and c['pattern'] not in ['retrieval','agent']:continue
   if isinstance(v,bool):v='Checked' if v else 'Unchecked'
   v={'local':'In this factory','external':'Outside this AI Factory','reference':'Reference capacity for independent work','independent':'Independent'}.get(str(v),v)
   definition,method=methods.get(k,('Explicit workload configuration.','Confirm the stated scenario assumption with the owner.'))
   add(c['name'],labels.get(k,k),v,'Explicit planning assumption' if k.startswith('reference_') or k in ['model','rate','calls','input_tokens','output_tokens'] else 'Selected',definition,method)
 for field,val,definition,method in [
 ('Infrastructure deployment profile','HGX B300 · Spectrum-X · Enterprise reference design with two network planes','Selects factory anchors rather than workload demand.','Architect selects a compatible catalogue profile.'),
 ('Sensitivity envelope','±30%','Explores faster and slower throughput assumptions.','Choose the agreed planning sensitivity. It is not a confidence interval.'),
 ('Use these planning assumptions','Checked','Accepts the displayed planning defaults.','Review defaults before calculating.'),
 ('Locally retained data in TB / Daily growth in GB','Blank','No local shared-storage amount is established. Blank is not zero.','Inventory actual local retained copies. Do not copy an outside corpus into this value.'),
 ('Initial dataset to load in TB / Initial loading window in hours','Blank','Initial transfer scope and time remain unresolved.','Obtain transfer volume and the allowed window from the data owner.'),
 ('Ongoing incoming / outgoing data in GB per day','Blank','Bulk daily transfer volumes remain unspecified.','Measure ingress and egress counters separately from model token traffic.'),
 ('Aggregate storage reads / writes in Gbps','Blank','Dedicated storage fabric throughput remains unresolved.','Measure directional read and write payload peaks. Capacity alone cannot determine bandwidth.'),
 ('East-west payload per GPU in Gbps / Customer datacenter round-trip target in ms','Blank','Collective traffic and latency objective remain unresolved.','Use GPU communication telemetry and an agreed RTT objective.'),
 ('Usable link fraction / Initial loading overlap','0.7 / Yes','Accepted network defaults. Storage networking is physically dedicated.','Review usable bandwidth and whether loading coincides with normal operation.'),
 ('Explanation connection','Manual: deterministic. Assisted: tested DeepSeek connection','Chooses prose generation without changing the calculation.','Configure an approved provider in AI connections. Backend credentials stay on the server.'),
 ('This saved result is public or fictional and may be sent to the selected provider','Checked only for this fictional assisted example','Permission to send the saved explanation packet to the chosen connection.','Leave unchecked for corporate data and select a connection approved for that data.')]:add('Shared',field,val,'Default or explicitly left blank',definition,method)
 table(['ID','Scope and exact field','Value','Basis'],[(r['id'],r['scope']+'\n[[field:'+r['field']+']]','[[value:'+r['value']+']]',r['basis']) for r in rows],[.45,3.1,5.1,1.95])
 para('Remaining displayed engine defaults: BF16 weights and KV cache, context 8192 tokens, 32 concurrent sequences, 8 GB workspace, compute efficiency 0.35 and memory efficiency 0.50. Host provisions are 256 GB RAM, 3840 GB local disk and 16 CPU cores per workload GPU. The blank growth horizon uses 365 days. Reference sizing does not use text-token equations.')
 page('Expected result and process')
 g=s['expected_gpu_counts'];table(['B300 workload GPUs','B200 workload GPUs','H200 workload GPUs','Selected B300 factory anchor'],[[g['HGX_B300'],g['HGX_B200'],g['HGX_H200'],s['expected_factory_gpus']]],[2.6,2.6,2.6,2.8])
 para('Describe the application → confirm its boundary → enter demand and assumptions → calculate GPU comparisons → prepare design handoff → explain the saved result → complete and retrieve the engagement.')
 para('The workload count and factory anchor are separate. Spare compute may support additional work, but it does not establish a qualified tenant count. Outstanding network and shared-storage measurements remain visible in the companion requirements.')
 for m in routes['manual']['maps']:
  heading(m['name']+' architecture');d.add_picture(str(ROOT/m['image']),width=Inches(10.3))
 page('Start and access the workspace')
 para('Complete the Mac installation guide in [[value:docs/macos-installation-guide.txt]]. From the repository folder run [[value:python3 deploy/local/run.py]]. Keep the terminal open. On first launch the application creates [[value:.anubis/identities.json]]. Open that private file locally, copy your identity token without quotation marks, and paste it into [[field:Access token]]. Click [[control:Open workspace]]. Saved cases persist in [[value:.anubis/anubis.sqlite]] across restarts. Preserve this directory and use the documented backup process.')
 para('For Copilot, put the provider API key in the protected backend configuration, never in the chat or input register. Open [[control:AI connections]], configure the approved provider and backend environment-variable name, and test the connection. The recorded assisted walkthrough uses DeepSeek deepseek-flash with low reasoning. Connection testing is separate from workload and explanation validation.')
 for mode,title in [('manual','Manual workflow'),('assisted','Copilot assisted workflow')]:
  page(title)
  para('Follow these numbered steps in order. Use a separate engagement name for this route. Input values are the same workload assumptions in both routes. In the assisted route, inspect extracted facts and explicitly enter any specialist reference values in the guided form.')
  t=table(['Step','Activity and exact values','Screen reference'],[],[.45,3.85,6.3])
  for i,st in enumerate(routes[mode]['steps'],1):
   cells=t.add_row().cells
   for cell,w in zip(cells,[.45,3.85,6.3]):cell.width=Inches(w)
   cells[0].text=str(i);render_inline(cells[1].paragraphs[0],st['text'].replace(';','.'));pic(cells[2],ROOT/st['image']);t.rows[-1]._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
 page('Compare and retrieve the results')
 table(['Check','Manual route','Copilot assisted route'],[['Workload GPU counts',f"B300 {g['HGX_B300']}, B200 {g['HGX_B200']}, H200 {g['HGX_H200']}",f"B300 {g['HGX_B300']}, B200 {g['HGX_B200']}, H200 {g['HGX_H200']}"],['Design handoff','Prepared with companion requirements','Prepared with companion requirements'],['Explanation','Saved deterministic narrative','Saved model-assisted narrative'],['Completion','Requirements delivered and saved','Requirements delivered and saved']],[2.3,4.15,4.15])
 para('Open the engagement from Cases and select Saved deliverables. Download the saved calculation, intake, brief and companion specification. Explain this to me retrieves narratives associated with that exact result. A later calculation does not update an earlier explanation. Refining demand requires a fresh deterministic calculation.')
 page('Appendix Parameter collection guide')
 table(['ID','Field and meaning','How to obtain or decide it','When unavailable'],[(r['id'],'[[field:'+r['field']+']]\n'+r['definition'],r['method'],'Record the unknown or an explicitly accepted assumption. Resolve any field listed by GPU estimate blocked before calculating.') for r in rows],[.45,3.1,4.5,2.55])
 page('Appendix Placement and explanation boundaries')
 table(['Term','Meaning and concrete examples'],[['Outside this AI Factory','Compute, search or storage beyond the capacity being designed. Examples include a customer GPU cluster, managed model API, customer datacenter search cluster, cloud search platform or an existing object store. It does not necessarily mean public Internet or a different site.'],['Source corpus and index','Original documents and the searchable index have separate storage and compute footprints. Examples include an NFS or SMB share, object storage, SharePoint and an OpenSearch index. Outside data is not automatically a local retained copy or initial transfer volume.'],['Model explanation','The LLM explains a saved result using a read-only packet. Numeric facts are inserted by the server. Invalid or unavailable model responses fall back to deterministic text. Qualitative prose remains interpretation, not a new engineering decision.'],['Reference capacity','Specialist counts use the exact per-hardware throughput and memory assumptions in the register. The example values are fictional planning assumptions. A complete independent group can be replicated. No linear scaling of a single larger job is inferred.'],['Validation scope','Both GUI routes were executed against the application and checked for matching GPU comparisons and saved handoffs. This validates the software workflow. It does not qualify real hardware performance, model quality, latency or live-provider reliability for every future request.']],[2.3,8.3])
 target=OUT/filename;d.save(target)
 (folder/'input-register.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(target,flush=True)
