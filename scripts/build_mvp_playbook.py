from pathlib import Path
import json,sys
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables/mvp-human-playbook';sys.path.insert(0,str(ROOT/'deliverables/usability'))
from playbook_typography import format_playbook,render_inline,install_styles
from placement_appendix import append_placement_guide
from parameter_definitions import DEFINITIONS
NAME='Cedar Engineering Review'
NOTES='Existing search and its 4 TB document corpus remain outside this AI Factory. No corpus copy is requested. Busy-hour demand is 2400 questions / 60 = 40 requests per minute. One model call per question. dense8b and 2000 input / 500 output tokens are explicit planning assumptions. No latency guarantee.'
DONE='Planning requirements delivered for architectural review. External document corpus remains outside this AI Factory. Network measurements remain to be confirmed.'
# One source for the input register and parameter collection appendix.
rows=[]
def add(field,value,basis,method):rows.append((f'I{len(rows)+1:02}',field,value,basis,method))
add('Customer workload name',NAME,'Entered','Choose a unique business name. Add your initials for your own run. Naming does not change sizing.')
add('Application pattern','Document or search assistant','Selected','Ask whether answers use retrieved documents. Follow one user question through the application. This case combines existing search with a local answer model.')
add('Factory users','One organisation','Default','Confirm the organisational boundary with the service owner. User counts do not establish multi-tenant isolation.')
add('Do activities run at the same time?','Yes — overlapping demand','Selected','Ask the application owner about operating windows. Separate windows require evidence of non-overlap. This example has one sized component.')
add('Component name 1','Engineering answers','Entered','Name the business activity. Use application documentation or a service map, not an internal compiler stage name.')
add('Compute location 1','In this factory','Default','Confirm where the answer model will execute. A deployment inventory or architecture diagram should place it inside this factory scope.')
add('Reserve dedicated capacity 1','Unchecked','Default','Ask whether capacity must remain exclusively reserved. Leave unchecked for this single activity. Do not infer reservations from user count.')
add('Search and indexing location 1','Existing service outside this AI Factory','Selected','Confirm ownership and hosting of retrieval, embedding and index refresh. An existing customer search cluster or managed cloud search service can be outside scope.')
add('Model preset','dense8b','Default accepted','Ask the model owner for model size and architecture. Here dense8b is a generic eight-billion-parameter planning assumption, not a named model benchmark.')
add('Describe demand using','Requests per minute','Default','Use application entry logs or gateway counters. Choose one demand basis to avoid adding users and requests twice.')
add('Peak requests per minute','40','Entered','Count 2,400 questions in the chosen busy hour and divide by 60. This is a busy-hour average. Shorter bursts require a separate measurement.')
add('Model calls per request or job','1','Entered','Trace complete requests using application logs or distributed tracing. Count retries and tool loops that invoke the model. This example explicitly assumes one call.')
add('Input tokens per model call','2000','Entered assumption','Tokenise representative prompts with the actual model tokenizer. Include retrieved passages, instructions and history. Use serving usage logs where available.')
add('Output tokens per model call','500','Entered assumption','Tokenise generated answers or collect completion-token counts from serving logs. Sample a representative busy period.')
add('Response target in seconds','Blank','Unresolved','Obtain the p95 completed-response objective and boundary from the service owner. It is a target, not a measured guarantee. Leave blank for this run.')
add('Locally retained data in TB','Blank','Unresolved','Inventory only factory-local data and copies. The 4 TB outside corpus is not an input here. Storage inventory tools or object-store reports can measure retained bytes.')
add('Daily growth in GB','Blank','Unresolved','Compare retained-byte inventories over multiple days. Separate net retention growth from total incoming traffic. Leave blank if unmeasured.')
add('Planning horizon in days','Blank uses 365','Preset retained','Confirm the capacity-planning period with the owner. This default has no added growth effect when local capacity and growth are unspecified.')
add('Initial dataset to load in TB','Blank','Unresolved','Confirm which bytes will actually cross the customer connection. No corpus copy is requested here. Do not substitute the outside corpus size.')
add('Initial loading window in hours','Blank','Unresolved','Ask operations how long a declared initial transfer may take. If no transfer is specified, leave the window unspecified too.')
add('Ongoing incoming data in GB per day','Blank','Unresolved','Measure additional bulk ingress from border counters or transfer logs. Separate it from request traffic. Daily totals do not establish peak bursts.')
add('Ongoing outgoing data in GB per day','Blank','Unresolved','Measure bulk exports beyond model responses using border counters and transfer logs. Leave blank when unmeasured, not zero.')
add('Usable link fraction','Blank uses 0.7','Preset retained','Network engineer reviews payload utilisation and protocol overhead. A 0.7 assumption is 70 percent usable link capacity, not a measured fact.')
add('Customer datacenter round-trip target in ms','Blank','Unresolved','Ask the network/service owner for the required boundary-to-boundary latency. Use timestamped probes to measure observed RTT separately.')
add('Aggregate storage reads in Gbps','Blank','Unresolved','Use storage telemetry or bytes read divided by the read window. Convert bytes/s to Gbps by multiplying by 8 and dividing by one billion. Capacity alone is insufficient.')
add('Aggregate storage writes in Gbps','Blank','Unresolved','Use peak concurrent write telemetry. Include initial load, ingestion and checkpoints when they overlap. Do not count an inclusive measured total twice.')
add('East-west payload per GPU in Gbps','Blank','Unresolved','Collect representative collective-communication or NIC counters per GPU with the platform engineer. Fabric type alone cannot supply a workload bandwidth measurement.')
add('Does initial loading overlap normal operation?','Yes — add the demands','Default','Confirm the loading schedule. This assumption matters only once transfer measurements exist. Separate phases would use the greater demand.')
add('Customer context and measurement notes',NOTES,'Entered','Record scope, arithmetic, provenance and unknowns in plain language. The 4 TB outside corpus belongs in this context, not the local storage field.')
add('Infrastructure deployment profile','HGX B300 GPUs · Spectrum-X network · Enterprise reference design with two network planes','Default','The architect selects the available deployment family. This version uses SX-HGXB300-DP-ENT-1.0.0. It supplies catalogue anchors, not proof of workload performance or NCP qualification.')
add('Sensitivity envelope','±30%','Default','A consultant-selected faster/slower throughput envelope. Keep the default for this run. It is not a statistical confidence interval.')
add('Use these planning assumptions','Checked','Accepted','Review model, memory, efficiency, host and network assumptions. Acceptance records a planning decision. It does not turn assumptions into measurements.')
add('Design project name',NAME,'Default','Keep the engagement name or your initialled variant so the handoff can be traced to the calculation.')
add('Intended candidate','planning:factory','Default','Choose the calculated factory candidate. It is a machine identifier for the saved deployment candidate, not another workload parameter.')
add('Design modelling platform','HGX_B300','Default','Keep B300 for this walkthrough. H200 and B200 comparison counts do not imply those platforms are selectable in the current handoff adapter.')
add('Modelling fabric choice','Spectrum-X','Default','Retain the selected profile fabric. The architect still validates topology, bandwidth and resilience.')
add('Accept the explicit modelling substitution and retain physical specifications outside the design tool','Unchecked','Default','Only accept if intentionally substituting a modelling platform and retaining physical differences outside the design tool. No substitution is selected here.')
add('Completion notes',DONE,'Entered','Record what was delivered and which measurements remain open. This is delivery documentation, not performance certification.')
add('I confirm that these selected requirements are delivered.','Checked','Confirmed','Confirm the saved calculation and handoff are the versions you intend to deliver.')
add('If newer edits exist, I explicitly intend to deliver this earlier saved calculation.','Unchecked','Default','Only check when knowingly delivering an earlier result after newer edits. This straight-through walkthrough does not require it.')
(OUT/'inputs.json').write_text(json.dumps(rows,indent=2)+'\n')
D=Document();sec=D.sections[0];sec.page_width=Inches(11.69);sec.page_height=Inches(8.27);sec.top_margin=sec.bottom_margin=Inches(.48);sec.left_margin=sec.right_margin=Inches(.55)
for n in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
 D.styles[n].font.name='Arial';D.styles[n].font.color.rgb=RGBColor(0,0,0)
D.styles['Normal'].font.size=Pt(10);D.styles['Normal'].paragraph_format.space_after=Pt(5);D.styles['Title'].font.size=Pt(25);D.styles['Heading 1'].font.size=Pt(18);D.styles['Heading 2'].font.size=Pt(12)
D.core_properties.title='Anubis MVP workload sizing playbook';D.core_properties.subject='Cedar Engineering manual workflow and human usability review';D.core_properties.author='Anubis'
sec.header.paragraphs[0].text='ANUBIS MVP 1.0  |  WORKLOAD SIZING PLAYBOOK'
f=sec.footer.paragraphs[0];f.text='Cedar Engineering  •  3 November 2026  •  Playbook revision 1.1                     ';x=OxmlElement('w:fldSimple');x.set(qn('w:instr'),'PAGE');f._p.append(x)
def table(head,data,widths):
 t=D.add_table(rows=1,cols=len(head));t.autofit=False;t.style='Table Grid'
 for c,w in zip(t.columns,widths):c.width=Inches(w)
 for c,v in zip(t.rows[0].cells,head):c.text=v
 for row in data:
  for c,v in zip(t.add_row().cells,row):c.text=str(v)
 for row in t.rows:
  row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
  for c,w in zip(row.cells,widths):c.width=Inches(w)
 for c in t.rows[0].cells:
  sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EEF1');c._tc.get_or_add_tcPr().append(sh)
  for run in c.paragraphs[0].runs:run.bold=True
 t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'));return t

def page(title):D.add_page_break();D.add_heading(title,1)
def pic(cell,file,w=6.6,h=5.1):
 im=Image.open(file);iw,ih=im.size;width=min(w,h*iw/ih)
 cell.paragraphs[0].add_run().add_picture(str(file),width=Inches(width))
def screenshot(name,crop=True):
 p=OUT/'screenshots'/f'{name}.png';im=Image.open(p)
 if name=='01-sign-in':
  im=im.crop((580,120,1340,1210));p=OUT/'screenshots'/f'{name}-crop.png';im.save(p)
 if name=='15-executive':
  im=im.crop((0,0,im.width,min(im.height,1010)));p=OUT/'screenshots'/f'{name}-crop.png';im.save(p)
 if crop and im.width==1920:
  im=im.crop((330,0,1900,im.height));p=OUT/'screenshots'/f'{name}-crop.png';im.save(p)
 return p
D.add_paragraph('Anubis workload sizing playbook','Title');D.add_paragraph('Cedar Engineering manual workflow and human usability review','Subtitle')
D.add_paragraph('Use this guide to turn a customer workload into a GPU estimate, prepare design inputs and retrieve a completed engagement. Follow the manual path from New engagement. No Copilot connection is needed.')
D.add_heading('The customer application',1)
D.add_paragraph('Cedar engineers ask 2,400 questions during the busiest hour. An answer model inside the AI Factory uses passages from an existing search system outside it. That search system indexes a 4 TB document corpus. No corpus copy is requested. This matters because the 4 TB stays outside the factory scope and must not automatically become local storage capacity or an initial network transfer. For this first estimate, assume one dense8b model call per question, with 2,000 input tokens and 500 output tokens. The intended outcome is comparable GPU estimates and a saved architecture handoff.')
D.add_heading('Workflow inputs',1)
D.add_paragraph('Use the exact values below. Add your initials to the engagement and project names for your own run. This changes only the name. Blank means unspecified, not zero. The collection appendix explains every input ID.')
# Short first register page, followed by bounded groups.
groups=[rows[:3],rows[3:9],rows[9:15],rows[15:21],rows[21:28],rows[28:32],rows[32:36],rows[36:]]
for i,g in enumerate(groups):
 if i:page('Workflow inputs continued')
 table(['ID','Workflow field','Definition and scope','Value or action','Basis'],[(i,f,DEFINITIONS[f],v,b) for i,f,v,b,m in g],[.4,2.0,3.1,4.0,1.05])
D.add_paragraph('Access credentials are excluded. GPU counts are outputs. The 4 TB corpus is context about a service outside this factory, not a local capacity input.')
page('Your system and the route through Anubis')
D.add_paragraph('Choose application → confirm placement → describe demand → calculate → prepare handoff → complete → retrieve. The diagram below shows the system you are describing, rather than the screens used to describe it.')
im=Image.open(OUT/'screenshots/10-system.png');im.crop((0,230,im.width,990)).save(OUT/'system-map.png');D.add_picture(str(OUT/'system-map.png'),width=Inches(10.3))
D.add_paragraph('Point 1 measures questions entering the application. Point 2 describes model work per question. Point 3 is optional local retention and remains unspecified. The search system is outside the dashed factory boundary. Its source corpus and search index are distinct quantities.')
steps=[
('Sign in','Open http://127.0.0.1:8787/. In Finder choose Go → Go to Folder and enter /Users/trai/Code/anubis/.anubis/. Open identities.json in a text editor. Copy the token value for local-owner without quotation marks.\n\nPaste it into [[field:Access token]] and click [[control:Open workspace]]. Keep the token private. The screenshot deliberately shows an empty field.\n\nIf already signed in, continue to step 2. If the file is missing, start python3 deploy/local/run.py from the repository.','01-sign-in'),
('Create the engagement','Select [[control:Cases]], then [[control:New engagement]]. Enter [[field:Customer workload name]] = [[value:Cedar Engineering Review]] plus your initials.\n\nClick [[control:Add Document or search assistant]] once. Scroll to the bottom and click [[control:Continue]].\n\nThis pattern describes an answer model using retrieved documents. Do not add a separate local search component because the search service already exists outside the factory.','03-choose'),
('Confirm the arrangement','Retain [[field:Factory users]] = [[value:One organisation]]. Select [[field:Do activities run at the same time?]] = [[value:Yes — overlapping demand]].\n\nA component is an application activity. Here component 1 is the answer service, not a server. Enter [[field:Component name 1]] = [[value:Engineering answers]]. Retain [[field:Compute location 1]] = [[value:In this factory]]. Leave [[field:Reserve dedicated capacity 1]] [[state:unchecked]].\n\nDifferent added activities can run in different places, such as a factory model and a cloud processing service. Search placement is set separately. Select [[field:Search and indexing location 1]] = [[value:Existing service outside this AI Factory]]. Click [[control:Continue]].','04-arrangement'),
('Describe demand','Retain [[field:Model preset]] = [[value:dense8b]] and [[field:Describe demand using]] = [[value:Requests per minute]].\n\nEnter [[field:Peak requests per minute]] = [[value:40]], [[field:Model calls per request or job]] = [[value:1]], [[field:Input tokens per model call]] = [[value:2000]] and [[field:Output tokens per model call]] = [[value:500]].\n\nThe busy-hour calculation is 2,400 ÷ 60 = 40 requests/minute. Remain on this page for steps 5 to 7.','05-demand'),
('Keep outside data outside','Leave [[control:Optional service target]] unchanged. Its response target is p95 time to the completed model response, not time to first token (TTFT). It excludes retrieval and external network time. Expand [[control:Data capacity and growth]].\n\nLeave [[field:Locally retained data in TB]] and [[field:Daily growth in GB]] [[state:blank]]. Leave [[field:Planning horizon in days]] [[state:blank]] to retain the displayed 365-day preset.\n\nThis retained-data field describes factory-local shared data, mapped to object storage by the guided MVP. It does not describe GPU-server local disks. Do not enter 4 TB here. It describes an outside corpus, not a factory-local copy. Blank also avoids claiming that every possible local cache requires zero storage.','06-data'),
('Review customer connectivity','Expand [[control:Factory networks and customer datacenter connection]].\n\nLeave [[field:Initial dataset to load in TB]], [[field:Initial loading window in hours]], [[field:Ongoing incoming data in GB per day]] and [[field:Ongoing outgoing data in GB per day]] [[state:blank]].\n\nThese inputs describe transfer demand, not the size of an outside repository. Their absence must remain visible in the result. Do not invent numbers to obtain a GPU estimate.','07-networks'),
('Retain network assumptions',f'Keep [[field:Usable link fraction]] [[state:blank]] to use 0.7. Leave the round-trip target, storage reads, storage writes and E-W payload fields [[state:blank]]. Keep [[field:Does initial loading overlap normal operation?]] = [[value:Yes — add the demands]].\n\nIn [[field:Customer context and measurement notes]], enter:\n\n[[value:{NOTES}]] Scroll down and click [[control:Continue]].\n\nThe storage network remains physically dedicated. Missing network measurements do not prevent this initial compute estimate.','08-network-policy'),
('Review and calculate','Retain the B300 Spectrum-X Enterprise profile shown and [[field:Sensitivity envelope]] = [[value:±30%]]. The profile supplies deployment sizes. It is not the customer application pattern.\n\nOptionally expand [[control:Inspect versioned planning defaults]] and compare the defaults appendix. Select [[control:Use these planning assumptions]]. Click [[control:Calculate estimate]].\n\nExpected destination: Analysis, with the architecture diagram and saved calculation.','09-review'),
('Read the requirements summary','Scroll to [[value:Your requirements at a glance]]. Distinguish the 8-GPU workload estimate from the 256-GPU selected factory deployment.\n\nClick [[control:Download requirements summary]]. This saves a readable text file. Check that unknown network quantities say [[value:Measurement required]].\n\nThe 256-GPU value comes from this selected catalogue profile. It is not a claim that every AI Factory must be that size.','11-summary'),
('Compare GPU options','Scroll to [[value:GPU workload comparison]]. Confirm B300 = 8, B200 = 8 and H200 = 8 GPUs. Required memory is about 58.36 GB per GPU.\n\nThese are complete eight-GPU-node estimates. Equal rounded counts do not establish equal performance or price. The 8–8 sensitivity range reflects rounding, not zero uncertainty.\n\nClick [[control:Download GPU comparison]] if you want the comparison JSON as a separate record.','12-gpus'),
('Check the four network roles','Read [[value:Four network requirements]]. Identify the external customer connection, north–south traffic, dedicated storage network and east–west GPU network.\n\nConfirm initial loading and storage throughput remain unmeasured. The outside corpus must not appear as a 4 TB initial transfer.\n\nScroll to the top and click [[control:Continue to Design handoff]]. This opens stage 4 using the saved calculation.','13-networks'),
('Prepare the handoff','Under [[value:Prepare an existing-field intake]], retain your project name, [[field:Intended candidate]] = [[value:planning:factory]], [[field:Design modelling platform]] = [[value:HGX_B300]] and [[field:Modelling fabric choice]] = [[value:Spectrum-X]].\n\nLeave the modelling-substitution checkbox [[state:unchecked]]. Click [[control:Prepare projection]].\n\nThis creates design inputs. It does not submit or approve a downstream architecture. H200 and B200 remain comparison options, not selectable handoff platforms here.','14-handoff'),
('Read and download the handoff','Read [[value:AI Factory design executive summary]]. Confirm it separates workload compute from factory provision.\n\nDownload [[control:Download executive summary]], [[control:Download design intake]] and [[control:Download companion specification]]. Scroll below the summary if needed to locate the buttons.\n\nKeep these together. The design intake carries supported fields. The companion specification carries additional requirements and unresolved measurements for your downstream AI Factory design tool or process.','15-executive'),
('Complete the engagement',f'Scroll to [[value:Complete this engagement]]. In [[field:Completion notes]], enter:\n\n[[value:{DONE}]]\n\nCheck [[field:I confirm that these selected requirements are delivered.]]. Leave the earlier-calculation acknowledgement [[state:unchecked]]. Click [[control:Complete engagement]].\n\nCompletion means requirements delivered. It does not certify hardware performance or approve the downstream design. Expected destination: Saved deliverables.','16-complete'),
('Confirm the saved version','On [[value:Saved deliverables]], confirm the engagement is completed and a completed version is listed.\n\nClick [[control:Download complete engagement record]]. Keep this JSON as the complete saved record. Expand [[control:Read saved executive summary]] if you want to reread the delivered narrative.\n\nDo not reopen for revisions during this first test. First verify that the completed result survives a page reload.','17-saved'),
('Find the completed case','Reload the browser. Select [[control:Cases]]. Find the row with your initialled engagement name.\n\nConfirm its status is [[value:Completed · requirements delivered]]. Click [[control:View engagement]].\n\nThe screenshot shows only the fictional case row. Other engagements on your computer may differ.','18-case'),
('Retrieve the same result','Confirm [[value:Saved deliverables]] opens for your case. Download the complete engagement record again. The saved calculation and projection should describe the same 8-GPU workload and 256-GPU deployment.\n\nYou have completed the workflow. Use the human review sheet to record where you hesitated, needed an explanation or saw a different outcome.\n\nUse [[control:Reopen engagement for revisions]] only for a subsequent experiment. Earlier completed versions remain preserved.','19-retrieved')]
for i,(title,text,screen) in enumerate(steps,1):
 page(f'Step {i} {title}')
 t=table(['Step','Activity and values','Screen reference'],[[str(i),text,'']],[.6,3.25,6.7]);pic(t.rows[1].cells[2],screenshot(screen),6.45,5.25)
 D.add_paragraph('Human review   □ Clear   □ Hesitated   □ Needed help   □ Could not complete     Notes: __________________________________')
page('Expected results and human review')
D.add_paragraph('Judge numerical reproduction and usability separately. A correct result reached only by guessing is a usability problem. Record the step number, what you expected, what happened and how you recovered.')
table(['Check','Expected result','Your observation'],[
('Demand','40 requests/minute or 0.666667 calls/second',''),('GPU comparisons','8 B300, 8 B200, 8 H200 GPUs',''),('Memory','58.359738 GB required per GPU',''),('Factory deployment','256 B300 GPUs under the selected profile',''),('Outside corpus','No local storage tier or initial transfer inferred from 4 TB',''),('Networks','Four roles visible. Dedicated storage fabric. Missing measurements explicit.',''),('Handoff','Executive summary, design intake and companion specification downloadable',''),('Closure and retrieval','Completed status. Saved record retrievable after reload.','')],[2.0,5.35,3.2])
D.add_paragraph('Understanding check: explain in your own words why the workload says 8 GPUs while the deployment says 256, why the outside 4 TB corpus is not local storage, and which requirements the architect must obtain from the companion specification.')
page('Human usability observations')
D.add_paragraph('Reviewer: __________________  Date: ______________  Start: __________  Finish: __________')
D.add_paragraph('Run without developer assistance first. At any unclear step, record the issue before looking for a workaround. If blocked, stop and preserve the case. Do not invent measurements to continue.')
table(['Step','Expected action or meaning','What was unclear or different','Impact and recovery'],[['','','',''] for _ in range(7)],[.5,3.0,4.2,2.85])
D.add_paragraph('Overall outcome   □ Completed unaided   □ Completed with help   □ Blocked\nConfidence explaining the result   □ Confident   □ Partly confident   □ Not confident\nMost important improvement: __________________________________________________________')
for offset in range(0,len(rows),5):
 page('Appendix Parameter collection guide')
 def unknown(row):
  return 'Leave unspecified until measured. Do not enter zero.' if row[3]=='Unresolved' else 'Use the listed planning assumption only after review. Otherwise clarify with the owner before accepting.'
 table(['ID','Parameter','Definition and scope','How to obtain or decide it','When unknown'],[(i,f,DEFINITIONS[f],m,unknown(r)) for r in rows[offset:offset+5] for i,f,v,b,m in [r]],[.4,1.8,3.05,3.6,1.7])
page('Appendix Retained calculation defaults')
p=json.loads((OUT/'result.json').read_text())['planning'];a=p['stage_calculations'][0]['assumptions'];pol=p['policy']
table(['Setting','Retained value','Meaning and source'],[
('Model parallelism',a['parallel_gpus'],'GPUs per model replica. Serving preset, not a hardware measurement.'),('Concurrent sequences',a['concurrent_sequences'],'Cache/batch planning assumption. Not the number of customer users.'),('Context allocation',a['context_tokens'],'Tokens allocated per sequence. Review with the serving engineer.'),('Weight and KV precision',f"{a['weight_bytes']} and {a['kv_bytes']} bytes",'Preset memory representation. Verify against actual serving configuration.'),('Workspace',a['workspace_GB']+' GB/GPU','Extra working memory. Measure the serving runtime for refinement.'),('Compute and memory efficiencies',pol['compute_efficiency']+' and '+pol['memory_efficiency'],'Analytical throughput assumptions. Refine with applicable benchmarks.'),('Host provision',a['host_ram_GB_per_gpu']+' GB RAM, '+a['local_disk_GB_per_gpu']+' GB disk, '+str(a['cpu_cores_per_gpu'])+' cores per GPU','Template allocation. Validate server resources during architecture design.'),('Traffic conversion',pol['bytes_per_token']+' bytes/token and '+pol['protocol_allowance']+' protocol allowance','Request traffic estimate. Measure actual application payloads for refinement.'),('Capacity policy','Full estimated service. No accepted shortfall. 90-day expansion lead.','Retained planning policy. Does not alter this single-node workload result.')],[2.2,3.0,5.35])
D.add_paragraph('The preset also contains training-only settings. They are inactive for this inference scenario. Input register values and the downloaded calculation preserve the active assumptions for reproduction.')
append_placement_guide(D,table)
# Shared glossary scenario name is parameterised locally without changing other guides.
for para in D.paragraphs:
 if 'For Bracken,' in para.text:para.text=para.text.replace('For Bracken,','For Cedar,')
page('Appendix Validation record and review limits')
D.add_paragraph('The documented manual journey was exercised against the installed application at http://127.0.0.1:8787 on 2 November 2026. The fictional Cedar Engineering Review engagement was calculated, projected, completed and retrieved after reload. The saved calculation matched the original. No application page errors were recorded.')
D.add_paragraph('Screenshots are captures of that application workflow. Some are cropped to retain the relevant controls. The sign-in image contains no credential. The run used browser automation as a synthetic end-user check. This establishes a reproducible starting point for your human review, not proof that the interface is intuitive.')
D.add_paragraph('Known presentation issue: the navigation footer still displays the legacy local-engine label v0.1. The MVP scope panel identifies MVP 1.0. Record this as a version-label inconsistency, not a change in the documented calculation.')
D.add_paragraph('This walkthrough does not qualify live Copilot interpretation, physical GPU performance or a downstream design submission. It tests the manual sizing and handoff workflow. Unmeasured network and storage requirements remain open by design.')
D.add_paragraph('If your result differs, retain the engagement and downloaded files. Record the differing field, profile and step. Case IDs, timestamps and an initialled name are expected to differ. Numerical settings and the selected profile should match.')
format_playbook(D)
# Headings stay black and remove any inherited title borders.
for style in D.styles:
 for border in list(style.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
for p0 in D.paragraphs:
 if p0.style.name in ['Title','Subtitle','Heading 1','Heading 2']:
  for run in p0.runs:run.font.color.rgb=RGBColor(0,0,0)
path=OUT/'Anubis_MVP_Cedar_Playbook_v1_1.docx';D.save(path)
# Delivery checks use the same source data as the appendix and register.
check=Document(path);text='\n'.join(p.text for p in check.paragraphs);cells='\n'.join(c.text for t in check.tables for r in t.rows for c in r.cells)
assert text.index('The customer application')<text.index('Workflow inputs')<text.index('Step 1 Sign in')
register=[t for t in check.tables if [c.text for c in t.rows[0].cells][:2]==['ID','Workflow field']]
appendix=[t for t in check.tables if [c.text for c in t.rows[0].cells][:2]==['ID','Parameter']]
for ident,field,*_ in rows:
 assert DEFINITIONS[field]
 assert any(r.cells[0].text==ident and r.cells[2].text==DEFINITIONS[field] for t in register for r in t.rows[1:])
 assert any(r.cells[0].text==ident and r.cells[2].text==DEFINITIONS[field] for t in appendix for r in t.rows[1:])
assert NOTES in cells and DONE in cells
assert 'I29 text' not in cells and 'Copy I38' not in cells
assert '[[' not in text+cells
assert len([t for t in check.tables if [c.text for c in t.rows[0].cells]==['Step','Activity and values','Screen reference']])==len(steps)
assert check.inline_shapes and ';' not in text+cells
(OUT/'document-validation.json').write_text(json.dumps({'input_ids':len(rows),'steps':len(steps),'screenshots_and_diagrams':len(check.inline_shapes),'register_appendix_coverage':True,'semantic_markup_resolved':True},indent=2))
print(path)
