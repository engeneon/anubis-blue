from pathlib import Path
import sys,json,hashlib
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image
R=Path('/Users/trai/Code/anubis-blue'); E=R/'testing-evidence/mac-install-2026-11-03'; O=R/'deliverables/mac-install-validation';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'deliverables/usability'))
from playbook_typography import install_styles,render_inline
ref=R/'docs/playbooks/S13_Nacre_Customer_Portal_Playbook.docx'
(E/'artifact.md').write_text('Design authority: '+str(ref)+'\nSHA256: '+hashlib.sha256(ref.read_bytes()).hexdigest()+'\nPreserve landscape A4, Arial, semantic field/value/control styles and bordered three-column numbered screenshot tables. Replace content with installation and a single manual S13 run. Header and footer updated for this purpose.\n')
d=Document(ref)
for x in list(d._element.body):
 if x.tag!=qn('w:sectPr'):d._element.body.remove(x)
s=d.sections[0];s.page_width=Inches(11.69);s.page_height=Inches(8.27);s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Inches(.5)
install_styles(d)
for n in ['Normal','Title','Heading 1','Heading 2']:
 d.styles[n].font.name='Arial';d.styles[n].font.color.rgb=RGBColor(0,0,0)
d.styles['Normal'].font.size=Pt(10);d.styles['Normal'].paragraph_format.space_after=Pt(5)
d.core_properties.author='Traiano Giuseppe Welcome';d.core_properties.title='Anubis Mac installation and first workload estimate';d.core_properties.comments='traiano@gmail.com'
s.header.paragraphs[0].text='ANUBIS  |  MAC INSTALLATION AND WORKLOAD PLAYBOOK'
s.footer.paragraphs[0].text='3 November 2026  |  Traiano Giuseppe Welcome  |  traiano@gmail.com'
def p(t):
 z=d.add_paragraph();render_inline(z,t);return z
def h(t,new=False):
 z=d.add_heading(t,1);z.paragraph_format.page_break_before=new

def table(headers,rows,widths):
 t=d.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.autofit=False
 for c,w in zip(t.columns,widths):c.width=Inches(w)
 for c,v,w in zip(t.rows[0].cells,headers,widths):c.width=Inches(w);render_inline(c.paragraphs[0],v)
 t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
 for row in rows:
  cs=t.add_row().cells
  for c,v,w in zip(cs,row,widths):c.width=Inches(w);render_inline(c.paragraphs[0],str(v))
  t.rows[-1]._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
 return t

def picture(cell,path):
 im=Image.open(path);w,hh=im.size;scale=min(6.05/w,4.5/hh)
 cell.paragraphs[0].add_run().add_picture(str(path),width=Inches(w*scale),height=Inches(hh*scale))
num=0
def workflow(title,steps):
 global num
 h(title,True)
 t=table(['Step','Activity and exact values','Screen reference'],[],[.45,3.85,6.3])
 for st in steps:
  num+=1;cs=t.add_row().cells
  for c,w in zip(cs,[.45,3.85,6.3]):c.width=Inches(w)
  cs[0].text=str(num);render_inline(cs[1].paragraphs[0],st['text']);picture(cs[2],st['image']);t.rows[-1]._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))

d.add_heading('Anubis Mac installation and first workload estimate',0)
p('Install Anubis, estimate a local customer portal fallback, prepare design inputs and retrieve a completed engagement after restarting. This walkthrough uses the manual route and the built-in deterministic explanation. No model-provider subscription or GPU hardware is needed.')
p('Reader key. [[field:UI field]] identifies a label. [[value:Entered value]] is literal content. [[control:Button]] identifies an action. [[state:Unchecked]] describes a setting.')
h('Customer scenario')
p('Nacre operates a customer portal whose main text service runs on an existing platform outside this AI Factory. It also wants a local continuity fallback for 20 requests per minute. Size only that explicit local fallback using a dense 8 billion parameter model, one model call per request, 2000 input tokens and 500 output tokens per call. These are fictional, accepted planning assumptions. The outside service does not silently become a local workload.')
h('Workflow input register')
rows=json.loads((R/'deliverables/complete-playbooks/S13/input-register.json').read_text())
rows[0]['value']='Nacre Customer Portal manual installation test'
rows[0]['definition']='Identifies this saved engagement.'
rows[0]['method']='Choose a recognisable name that distinguishes this installation test.'
for r in rows:
 if r['field']=='Application pattern':r['value']='Direct model service'
 if r['field']=='Explanation connection':r['value']='Deterministic explanation — no model';r['basis']='Selected for this run';r['method']='Choose the built-in deterministic option. No provider connection is needed.'
 if r['field'].startswith('This saved result'):r['value']='Unchecked';r['basis']='No provider transmission'
for f,v,definition,method in [
 ('Reserve dedicated capacity 1 and 2','Unchecked','Neither activity reserves a dedicated pool.','Confirm reservation policy with the workload owner.'),
 ('Describe demand using','Requests per minute','Unit of incoming application demand.','Use request counters from the application gateway.'),
 ('Design modelling platform / Modelling fabric choice','HGX_B300 / Spectrum-X','Chosen downstream modelling options.','Select an architect-approved available platform and fabric. This is not a bandwidth measurement.'),
 ('Intended candidate','First planning candidate','Factory candidate used for the projection.','Select the candidate associated with this saved calculation.'),
 ('Completion notes','Planning requirements and explanation delivered. Outstanding network and storage measurements remain in the companion specification.','Records the scope of delivery.','Record unresolved requirements explicitly.'),
 ('I confirm that these selected requirements are delivered.','Checked','Closes the engagement with its selected deliverables.','Review the exports before confirming.')]:rows.append(dict(scope='Shared',field=f,value=v,basis='Entered or selected',definition=definition,method=method))
for i,r in enumerate(rows,1):r['id']=f'I{i:02}'
(E/'input-register.json').write_text(json.dumps(rows,indent=2))
table(['ID','Field and scope','Meaning','Value and basis'],[(r['id'],'[[field:'+r['field']+']]\n'+r['scope'],r['definition'],'[[value:'+r['value']+']]\n'+r['basis']) for r in rows],[.45,3.0,3.05,4.1])
p('Displayed engine defaults retained: BF16 weights and KV cache, context 8192 tokens, 32 concurrent sequences, 8 GB workspace, compute efficiency 0.35 and memory efficiency 0.50. Host provisions are 256 GB RAM, 3840 GB local disk and 16 CPU cores per workload GPU. The blank growth horizon uses 365 days. These are planning presets, not measurements.')
h('Architecture and route to the result',True)
p('Install and sign in → describe the two services → confirm placement → enter local demand → calculate → prepare design handoff → explain → complete → retrieve. The diagram labels indicate where computation is located. Only the local fallback contributes model compute to this factory estimate.')
a=json.loads((E/'flow/S13/manual.json').read_text())
for m in a['maps']:
 p(m['name']).paragraph_format.keep_with_next=True;d.add_picture(m['image'],width=Inches(9.6))
inst=[
 ('Open Terminal. Install Apple command-line tools if absent with [[value:xcode-select --install]]. Install Homebrew using https://docs.brew.sh/Installation. Then run [[value:brew install cmake node openssl@3 sqlite python]]. Existing prerequisites were reused on this Mac. Screenshot: published guide reference.','install-tools.png'),
 ('In a permanent folder run [[value:git clone https://github.com/engeneon/anubis-blue.git anubis-blue-install-validation-20261103]]. Run [[value:cd anubis-blue-install-validation-20261103]]. Run [[value:git rev-parse HEAD]] to identify the checkout. This run used main commit dff91d4bc7ab07d563683c3b24583df7f2e4baa8. Screenshot: guide reference.','install-build.png'),
 ('From that folder run each command separately:\n[[value:cmake --preset local -DCMAKE_PREFIX_PATH="$(brew --prefix openssl@3);$(brew --prefix sqlite)"]]\n[[value:cmake --build --preset local -j4]]\n[[value:npm ci --ignore-scripts]]\n[[value:npm run build]]\n[[value:ctest --test-dir build --output-on-failure]]\nAll five commands completed successfully. Screenshot: guide reference.','install-build.png'),
 ('Run [[value:python3 deploy/local/run.py --port 8791]]. Leave Terminal open. Open [[value:http://127.0.0.1:8791]]. This port keeps the existing installation separate. The current launcher also prints 8787 incorrectly. Use 8791 for this walkthrough. Screenshot: token instructions in the guide.','install-token.png'),
 ('In another Terminal window, change to this same clone. Run [[value:open -a TextEdit .anubis/identities.json]]. Find [[value:local-owner]] and copy only its token text, without quotation marks. The launcher creates this file on first start. Do not edit or share it. Screenshot: guide reference.','install-token.png')]
workflow('Install and bootstrap access',[dict(text=t,image=str(E/im)) for t,im in inst])
steps=a['steps']
steps[5]['text']='Click [[control:Continue]]. '+steps[5]['text']
steps[7]['text']='Select [[control:Local continuity fallback]]. '+steps[7]['text']
steps[10]['text']='Click [[control:2 Confirm arrangement]] to review the architecture diagrams, then click [[control:4 Review and estimate]]. '+steps[10]['text']
steps[12]['text']='Click [[control:Continue to Design handoff]]. '+steps[12]['text']
steps[14]['text']='Read the executive summary. Click [[control:Download design intake]], [[control:Download companion specification]] and [[control:Download executive summary]]. Unresolved network and storage measurements remain explicit.'
steps[16]['text']='Read the saved explanation of workload GPUs, the deployment anchor, memory, storage and network roles. Keep the panel open and continue below.'
workflow('Describe calculate and complete the workload',steps)
workflow('Restart and retrieve the saved engagement',json.loads((E/'retrieval-steps.json').read_text())['steps'])
h('What the completed result means',True)
table(['Requirement','Observed result','Design implication'],[
 ['B300 workload GPUs','8','Local continuity fallback under the accepted assumptions.'],['B200 workload GPUs','8','Alternative hardware estimate for the same workload.'],['H200 workload GPUs','8','Alternative hardware estimate for the same workload.'],['Factory deployment anchor','256 GPUs','The selected reference-design anchor is separate from workload demand. Spare compute does not establish a qualified tenant count.'],['Shared storage and network throughput','Unresolved measurements retained','Do not treat blanks as zero or as qualified capacity.'],['Design handoff','Prepared and downloaded','Intake and companion specification must travel together.'],['Engagement and restart','Completed and retrieved','The same token, saved result and explanation survived restart.']],[2.4,2.4,5.8])
p('East-west connectivity follows the selected fabric profile. North-south service traffic, customer-datacenter ingress and egress, and a physically dedicated storage network remain separate design concerns. This scenario supplies no measured transfer volumes or storage throughput, so the result does not claim final link capacities for them. The companion specification preserves these gaps for the downstream AI Factory design tool or process.')
h('Appendix Parameter collection guide',True)
table(['ID','Field and definition','How to obtain or decide it','When unknown'],[(r['id'],'[[field:'+r['field']+']]\n'+r['definition'],r['method'],'Record an explicit assumption or leave optional measurements unresolved. Resolve fields identified by GPU estimate readiness before calculating.') for r in rows],[.45,3.1,4.5,2.55])
h('Appendix Placement access and persistence',True)
p('Outside this AI Factory means a system beyond the compute and storage capacity being designed. Valid examples include a customer GPU cluster, a managed model API, a cloud search platform, an existing customer datacenter search cluster or an existing object store. It does not necessarily mean the public Internet or a different physical site.')
p('A source document corpus, searchable index, local retained copy and initial transfer are distinct quantities. Do not copy one into another without confirming the actual data flow. Existing NFS or SMB shares, SharePoint, S3-compatible object storage and OpenSearch are possible outside systems.')
p('Stop the foreground service with Control C. Restart from the same clone with the same command and port. Keep the .anubis directory, including anubis.sqlite and identities.json. Deleting it or launching a different clone creates a different local workspace. Follow the repository backup instructions before moving or upgrading an installation.')
h('Appendix Installation and acceptance evidence',True)
p('Baseline tested: main dff91d4bc7ab07d563683c3b24583df7f2e4baa8. Apple Silicon Mac running macOS 26.5.2. A fresh permanent clone, fresh application database and separate port were used. Existing Homebrew and developer tools were reused. This tests source installation on this Mac, not a pristine operating system or Intel Mac.')
table(['Check','Result','Evidence'],[['Clone and checkout','Pass','01-clone.log and environment.json'],['Configure and compile','Pass','02-configure.log and 03-build.log'],['Install UI dependencies and build','Pass','04-npm-ci.log and 05-ui-build.log'],['CTest','Pass with no failed tests','06-ctest.log'],['Manual GUI scenario','Pass','21 recorded workflow steps and saved exports'],['Restart and retrieval','Pass','restart-validation.json and retrieval-steps.json'],['Live Copilot and physical hardware','Not tested','This walkthrough uses deterministic explanation and planning estimates.']],[2.5,2.6,5.5])
p('Installation screenshots show the published guide as a navigation reference. Command execution results are supported by the saved logs. Workload and retrieval screenshots show the actual fresh application instance. Credentials are excluded.')
h('Customer issue awaiting approval')
p('When --port 8791 is supplied, the launcher initially prints 8787 before the backend reports 8791. A customer could open the wrong installation and receive a token rejection. The service itself works at the selected port. Proposed remediation: report only the effective address and add a regression check. No product remediation has been applied. The tested installation and manual scenario completed without a blocking failure.')
p('Anubis is distributed under Apache License 2.0. Preserve the repository LICENSE and NOTICE. See docs/licensing.md for attribution guidance.')
d.save(O/'Anubis_Mac_Installation_Nacre_Playbook.docx')
(E/'validation-summary.json').write_text(json.dumps(dict(commit='dff91d4bc7ab07d563683c3b24583df7f2e4baa8',installation='passed',scenario='S13 manual passed',gpu_counts=dict(B300=8,B200=8,H200=8),factory_anchor=256,restart='passed',product_changes=False,issue='Custom-port startup message prints incorrect default address. Remediation awaiting approval.'),indent=2))
print(O/'Anubis_Mac_Installation_Nacre_Playbook.docx')
