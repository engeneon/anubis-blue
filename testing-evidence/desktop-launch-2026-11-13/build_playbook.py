from pathlib import Path
import sys,json,hashlib
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image
R=Path(__file__).resolve().parents[2];E=R/'testing-evidence/desktop-launch-2026-11-13';O=R/'deliverables/neon-launch-2026-11-13'
sys.path.insert(0,str(R/'deliverables/usability'))
from playbook_typography import install_styles,render_inline
ref=R/'deliverables/mac-install-validation/Anubis_Mac_Installation_Nacre_Playbook.docx'
(E/'artifact.md').write_text('Reference '+str(ref)+'\nSHA256 '+hashlib.sha256(ref.read_bytes()).hexdigest()+'\nPreserve landscape A4, Arial body and semantic UI styles. Preserve numbered three-column screenshot workflow. Replace scenario and installation content for desktop DMG. New suite positioning is explicitly requested.\n')
d=Document(ref)
for x in list(d._element.body):
 if x.tag!=qn('w:sectPr'):d._element.body.remove(x)
install_styles(d);sec=d.sections[0]
sec.header.paragraphs[0].text='NEON AI FACTORY ARCHITECT  |  ANUBIS WORKLOAD SIZING'
sec.footer.paragraphs[0].text='13 November 2026  |  Traiano Giuseppe Welcome  |  traiano@gmail.com'
d.core_properties.title='Anubis desktop workload sizing playbook';d.core_properties.author='Traiano Giuseppe Welcome';d.core_properties.comments='traiano@gmail.com'
def p(text):
 q=d.add_paragraph();render_inline(q,text);return q
def h(text,new=False):
 q=d.add_heading(text,1);q.paragraph_format.page_break_before=new

def table(headers,rows,widths):
 t=d.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.autofit=False
 for col,w in zip(t.columns,widths):col.width=Inches(w)
 for c,v,w in zip(t.rows[0].cells,headers,widths):c.width=Inches(w);render_inline(c.paragraphs[0],v)
 t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
 for row in rows:
  cs=t.add_row().cells
  for c,v,w in zip(cs,row,widths):c.width=Inches(w);render_inline(c.paragraphs[0],str(v))
  t.rows[-1]._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
 return t

def pic(c,path):
 im=Image.open(path);w,hh=im.size;scale=min(6.15/w,4.95/hh)
 c.paragraphs[0].add_run().add_picture(str(path),width=Inches(w*scale),height=Inches(hh*scale))
rows=[]
def add(field,value,definition,method,basis='Explicit fictional planning assumption',unknown='Confirm with the workload owner before using a customer estimate.'):
 rows.append(dict(id=f'I{len(rows)+1:02}',field=field,value=value,definition=definition,method=method,basis=basis,unknown=unknown))
add('Customer workload name','Peregrine Product Lab — desktop walkthrough','The saved engagement name.','Agree a unique customer and application name.','Entered label')
add('Application pattern','Document or search assistant','Search information before generating an answer.','Walk through a representative task with the application owner.','Selected architecture')
add('Factory users','One organisation','Organisations sharing the factory.','Confirm tenancy and commercial scope.','Selected')
add('Do activities run at the same time?','Yes — overlapping demand','Whether activity demand may coincide.','Review job schedules and gateway traffic during busy periods.','Selected')
add('Component name 1','Proposed assistant','A business activity, not a hardware node.','Name the activity with the application owner.','Entered label')
add('Compute location 1','In this factory','The answer model consumes local GPU capacity.','Confirm the intended deployment boundary.','Selected')
add('Search and indexing location 1','Existing service outside this AI Factory','Search, embeddings and index refresh remain on an existing service.','Ask the search owner where queries, embedding and indexing run. Record the source corpus separately.','Confirmed scenario boundary')
add('Reserve dedicated capacity 1','Unchecked','No dedicated reservation is requested for this activity.','Confirm isolation and reservation policy.','Retained default')
add('Sizing method','Analytical model','Use the supported dense-model equations.','Use this method for a supported model. Specialist work needs scoped reference capacity.','Retained default')
add('Model preset','dense8b · planning assumption','Generic dense 8 billion parameter model.','Read the model registry and serving configuration. If not selected, accept a named planning preset.')
add('Describe demand using','Requests per minute','Application arrivals in a busy period.','Choose one demand representation to avoid double counting.','Selected')
add('Peak requests per minute','40','Busy-period requests across the whole assistant.','Count gateway requests in minute buckets over a representative peak. Employee count alone cannot supply this number.')
add('Model calls per request or job','1','Total model invocations per completed request.','Inspect distributed traces and include retries or loops.')
add('Input tokens per model call','2000','Prompt, history and retrieved passages per call.','Read prompt-token metrics or tokenize complete representative prompts with the actual model tokenizer.')
add('Output tokens per model call','500','Generated answer tokens per call.','Read completion-token metrics or tokenize representative responses.')
notes='Fictional planning assumptions. 5000 employees is context, not demand. Local answer model uses an existing search service outside this AI Factory. No local corpus copy or initial transfer volume is specified.'
add('Customer context and measurement notes',notes,'Scope and provenance for this planning estimate.','Record measurement dates, owners, uncertainty and external dependencies.','Entered context')
add('Optional service target','Blank','No time-to-first-token or complete-response objective is asserted.','Agree the metric, percentile and measurement boundaries.','Unspecified','Leave unresolved. The estimate does not guarantee latency.')
add('Data capacity and growth','All optional fields blank','No local shared-storage capacity, retained corpus copy or growth volume is established.','Inventory retained local copies and growth with the data owner. Use storage counters and retention policy.','Unspecified','Leave blank rather than infer a local copy from the outside source.')
add('Factory networks and customer datacenter connection','Optional measurement fields blank','Initial transfer, loading window, bulk transfers, storage rates, E-W payload and latency remain unknown.','Use transfer logs for bytes and duration, directional interface counters for busy-period rates, storage telemetry for reads/writes and collective benchmarks for E-W.','Unspecified','Keep as follow-up items. Do not convert blanks to zero.')
add('Network planning defaults','Dedicated storage fabric, usable fraction 0.7, initial loading overlaps normal operation','Baseline network policy and utilization assumptions.','Review usable bandwidth and overlap with the network architect.','Retained defaults')
add('Infrastructure deployment profile','HGX B300 GPUs · Spectrum-X network · Enterprise reference design with two network planes','Catalogue family providing supported factory anchors.','Architect selects an applicable reference profile. This selection is not certification.','Retained default')
add('Sensitivity envelope','±30%','Variation in assumed throughput.','Agree a planning sensitivity and refine with applicable evidence.','Retained default')
add('Use these planning assumptions','Checked','Accept the displayed model and capacity assumptions.','Review preset memory and efficiency parameters before calculating.','Explicit acceptance')
add('Design project name / Intended candidate','Peregrine Product Lab — desktop walkthrough / planning:factory','Links the design handoff to this result.','Retain the engagement name and calculated factory candidate.','Retained defaults')
add('Design modelling platform / Modelling fabric choice','HGX_B300 / Spectrum-X','Platform and fabric used in the downstream architecture model.','Select compatible modelling values. Keep physical and performance validation explicit.','Retained defaults')
add('Accept the explicit modelling substitution and retain physical specifications outside the design tool','Unchecked','No substitute platform is being acknowledged.','Check only when a documented substitution is actually needed.','Retained default')
add('Explanation connection / provider transmission','Deterministic explanation — no model / Unchecked','Generate prose from saved facts without sending them to a provider.','Choose the built-in option. A configured Copilot is optional.','Selected')
add('Consultant notes (optional)','Planning requirements delivered. Network and shared-storage measurements remain explicit follow-up items.','Delivery scope recorded at closure.','List unresolved responsibilities and next measurements.','Entered')
add('I confirm that these selected requirements are delivered.','Checked','Close and preserve this delivery.','Review selected calculation and projection before confirming.','Explicit acceptance')
add('If newer edits exist, I explicitly intend to deliver this earlier saved calculation.','Unchecked','Do not override a newer calculation.','Use only after deliberately reviewing an earlier version.','Retained default')
(E/'input-register.json').write_text(json.dumps(rows,indent=2))
d.add_heading('Anubis desktop workload sizing playbook',0)
p('Follow Peregrine Product Lab from an application description to GPU estimates, design inputs and a saved engagement. Anubis is the workload-sizing component of the Neon AI Factory Architect suite. It establishes planning requirements for architectural review.')
p('Reader key. [[field:UI field]] identifies a label. [[value:Entered value]] is literal text. [[control:Button]] identifies an action. [[state:Unchecked]] describes a setting.')
h('Customer scenario')
p('Peregrine wants an assistant for approximately 5000 employees. A consultant has resolved the initial uncertainty: the answer model will run inside the factory, using passages from an existing search service outside it. The accepted planning demand is 40 questions per minute. The model is dense8b, with one call, 2000 input tokens and 500 output tokens per question. These fictional assumptions describe the workload to estimate. Employee count is context, not a sizing multiplier. No local corpus copy or initial bulk transfer is specified.')
h('Workflow input register')
table(['ID','Exact UI field','Definition and scope','Value or action','Basis'],[(x['id'],'[[field:'+x['field']+']]',x['definition'],'[[value:'+x['value']+']]',x['basis']) for x in rows],[.4,2.35,2.65,3.45,1.75])
h('Understand the architecture',True)
p('The model service is inside the factory. Search and its index are outside. The numbered measurement points connect application demand, model work and retained data to the sizing inputs. A retained-data box in the diagram is not proof that a local copy is required.')
im=Image.open(E/'architecture.png');w,hh=im.size;im.crop((int(w*.19),int(hh*.41),int(w*.97),hh)).save(E/'architecture-crop.png');d.add_picture(str(E/'architecture-crop.png'),width=Inches(10.35))
p('Describe → confirm placement → enter scale → calculate → prepare handoff → explain → complete → retrieve. The manual route needs no model-provider account. An optional Copilot can support interpretation without changing the deterministic sizing engine.')
h('Install and access Anubis',True)
p('On an Apple Silicon Mac running macOS 13 or later, quit an existing Anubis instance. Open [[value:Anubis-0.0.1-macos-arm64.dmg]], drag [[value:Anubis.app]] to [[value:Applications]] and choose [[control:Replace]] if prompted. Open Anubis from Applications. The supplied build was accepted by Gatekeeper as a notarized Developer ID application on the test Mac.')
p('The desktop app manages its local service and opened an authenticated workspace during this walkthrough. If an access-token screen appears, use the macOS menu [[control:Anubis → Copy Access Token]], paste into [[field:Access token]] and select [[control:Open workspace]]. Never include a token in a screenshot or workload description. [[control:Anubis → Show Data Folder]] locates the persistent case database and identity file. Preserve and back up this folder before moving installations.')
p('For this Mac, the data folder is [[value:~/Library/Application Support/Anubis]]. Installing the application bundle does not require deleting that folder. The built-in browser service used port 8788 during this run. Use the desktop app or [[control:Anubis → Open in Browser]] rather than assuming a fixed port.')
h('Work through the scenario',True)
steps=json.loads((E/'steps.json').read_text())
steps[3]['text']=steps[3]['text'].replace('Enter the customer context shown in the input register.','Set [[field:Customer context and measurement notes]] = [[value:'+notes+']]. Leave optional service, data and network measurement fields blank.')
steps[8]['text']='After preparing the projection, scroll below the form to [[control:AI Factory design executive summary]]. Review the workload and factory counts. Download the executive summary, design intake, readable architecture brief and companion specification. In each macOS Save dialog, choose a location and click [[control:Save]]. The screenshot shows the form and the beginning of the summary below it.'
t=table(['Step','Activity and exact values','Screenshot'],[],[.45,3.85,6.3])
for i,st in enumerate(steps,1):
 cs=t.add_row().cells
 for c,ww in zip(cs,[.45,3.85,6.3]):c.width=Inches(ww)
 cs[0].text=str(i);render_inline(cs[1].paragraphs[0],st['text'])
 source=E/Path(st['image']).name;im=Image.open(source);ww,hh=im.size
 # Preserve actual pixels, crop only unused desktop/sidebar context for legibility.
 if i in [3,4,5,6,7,8,9,13]:box=(int(ww*.17),int(hh*.035),int(ww*.98),hh)
 elif i in [10,11,12,19]:box=(int(ww*.19),int(hh*.08),int(ww*.94),int(hh*.97))
 else:box=(0,0,ww,hh)
 target=E/f'playbook-step-{i:02}.png';im.crop(box).save(target);pic(cs[2],target)
 t.rows[-1]._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
h('Interpret the result',True)
table(['Output','Result','Design meaning'],[['B300 / B200 / H200 workload GPUs','8 / 8 / 8','Each rounds to one supported 8-GPU node. Equal counts do not imply equal throughput or price.'],['Selected B300 factory anchor','256 GPUs','Separate reference-profile deployment size. The workload itself is not 256 GPUs.'],['Per-GPU memory requirement','58.36 GB','A per-device feasibility check, not a shared-storage requirement.'],['Host provisions for the workload','2048 GB RAM, 30720 GB local disk, 128 CPU cores','Planning defaults. They require server-design review.'],['Potential workload copies at the anchor','32 in compute terms','Conditional copies of the same profile. Network, storage, isolation and tenancy must also support them.'],['External and N-S application traffic','About 0.000073 Gbps incoming and 0.000019 Gbps outgoing','Declared model-traffic lower bounds. Initial load and other payloads remain unresolved. These are not selected circuit sizes.'],['Storage and four network roles','Open measurements retained','E-W fabric is Spectrum-X. Storage fabric is physically dedicated Ethernet. Bulk ingress, capacity, I/O and latency need measurement.'],['Handoff and closure','Delivered and saved','Supported fields map to intake. Apply remaining companion requirements during Neon architecture design.']],[2.45,2.65,5.5])
p('The deterministic calculation provides planning evidence. Neon AI Factory Architect uses the supported intake parameters to develop an architecture. The companion brief carries requirements that do not fit the intake fields. This walkthrough validates export and retrieval, not an automatic or live Neon design submission.')
h('Appendix How to obtain the inputs',True)
table(['ID','Exact parameter','Definition and scope','How to obtain or decide it','When unknown'],[(x['id'],'[[field:'+x['field']+']]',x['definition'],x['method'],x['unknown']) for x in rows],[.4,2.25,2.45,3.45,2.05])
p('Preset details retained by the engine: BF16 weights and KV cache, context 8192 tokens, 32 concurrent sequences, 8 GB workspace, compute efficiency 0.35 and memory efficiency 0.50. Host provisions are 256 GB RAM, 3840 GB local disk and 16 CPU cores per workload GPU. These defaults should be reviewed against the intended serving stack.')
h('Appendix Placement and saved work',True)
p('Outside this AI Factory means beyond the compute or storage capacity being designed. Examples include an existing customer datacenter search cluster, a managed cloud search service, a customer GPU cluster or a model API. The term does not imply the public Internet or a different physical site. Source documents may reside in an NFS or SMB share, SharePoint or object storage, while their index resides elsewhere.')
p('Source corpus, search index, retained local copy and initial transfer are separate quantities. Confirm each with its owner. No local shared-storage capacity in this scenario means unresolved scope, not zero storage demand. GPU-server disks are separately provisioned.')
p('Cases and completed versions persist in the desktop data folder. After restarting, select Cases, then View engagement. Saved deliverables retains the exact calculation, projection and explanation. Reopen for revisions only when starting a new revision.')
h('Appendix Validation and release record',True)
v=json.loads((E/'validation.json').read_text())
table(['Check','Observed result'],[['Installer','Anubis 0.0.1, macOS arm64. Installed over the previous bundle. Existing data folder preserved.'],['Signing','Gatekeeper accepted Notarized Developer ID. codesign verification passed.'],['Scenario','S15 selected randomly from the canonical 16-scenario catalogue.'],['GUI result','8 GPUs for each of B300, B200 and H200. Factory candidate 256 GPUs.'],['Saved result',v['result_id']],['Projection',v['projection_id']],['Exports','GPU comparison, design intake, companion specification, architecture brief, executive summary, explanation and complete engagement downloaded.'],['Persistence','Completed status and saved explanation retrieved after restarting the desktop app.'],['Customer blocking failures','None encountered in this manual scenario.'],['Qualification scope','One actual desktop GUI scenario. No live Copilot, physical GPU performance or live Neon submission tested.'],['Distribution','Installer and updated documentation are prepared locally. Publishing the download page is a separate release step.']],[2.4,8.2])
p('Author: Traiano Giuseppe Welcome. Email: traiano@gmail.com. Anubis is free for personal and commercial use under Apache License 2.0. Preserve LICENSE, NOTICE and applicable third-party attribution. See docs/licensing.md.')
target=O/'Anubis_Desktop_Peregrine_Playbook.docx';d.save(target);print(target)
