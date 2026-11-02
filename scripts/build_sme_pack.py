"""Build the SME documents from reviewed text and captured GUI evidence."""
from pathlib import Path
import json,re,sys,hashlib,shutil,datetime
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables/sme-evaluation-2026-11-02';SRC=OUT/'source';DOC=OUT/'documents';DOC.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'deliverables/usability'))
from playbook_typography import install_styles,render_inline
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
def diagram(name):
 im=Image.new('RGB',(1600,620),'white');dr=ImageDraw.Draw(im)
 def box(x,y,w,h,title,lines):
  dr.rounded_rectangle((x,y,x+w,y+h),14,fill='#eef3f7',outline='#17365d',width=3)
  for i,t in enumerate([title]+lines):dr.text((x+18,y+17+36*i),t,font=ImageFont.truetype(FONT,25 if i else 27),fill='#17365d')
 def ar(x,y,a,b):
  dr.line((x,y,a,b),fill='#185b45',width=4);dr.polygon([(a,b),(a-13,b-8),(a-13,b+8)],fill='#185b45')
 if name=='method':
  for i,(t,ls) in enumerate([('Describe',['Intent and pattern','Local or outside']),('Measure',['Demand and tokens','Assumptions']),('Calculate',['GPU alternatives','Supporting resources']),('Select',['Deployment anchor','Limits and gaps']),('Deliver',['Design intake','Saved outcome'])]):
   box(10+i*320,140,300,155,t,ls)
   if i<4:ar(310+i*320,210,327+i*320,210)
  dr.text((280,370),'Refine the evidence and create a new calculation. Preserve the previous result.',font=ImageFont.truetype(FONT,28),fill='#185b45')
 elif name=='network':
  box(10,180,340,155,'Customer datacenter',['Source data and users','Outside this factory']);box(510,180,350,155,'Factory boundary',['North-south traffic','Ingress and egress']);box(1060,30,510,155,'GPU compute',['East-west fabric','Workload communication']);box(1060,400,510,155,'Storage services',['Dedicated storage network','Capacity and I/O rates']);ar(350,260,510,260);dr.text((350,140),'External link',font=ImageFont.truetype(FONT,24),fill='#185b45');ar(860,260,1060,110);ar(860,260,1060,470);dr.line((1320,185,1320,400),fill='#185b45',width=4)
 elif name=='application':
  box(10,200,350,155,'Engineers',['2,400 questions/hour','40 questions/minute']);box(570,200,470,155,'Local answer model',['dense8b planning preset','2,000 in / 500 out tokens']);box(570,10,470,135,'Outside search service',['4 TB source corpus','No implied local copy']);ar(360,275,570,275);dr.line((805,145,805,200),fill='#185b45',width=4);box(1180,200,400,155,'Answer',['One model call/question','Latency to be measured']);ar(1040,275,1180,275);dr.text((530,455),'Factory scope includes the answer model. Search and corpus remain outside.',font=ImageFont.truetype(FONT,26),fill='#185b45')
 else:
  box(10,80,420,160,'Consultant browser',['Guided builder or Copilot','Review and acceptance']);box(575,80,450,160,'Application and API',['Cases, versions and jobs','Authorization and lifecycle']);box(1160,80,420,160,'Deterministic core',['Demand and resource model','Projection and explanations']);ar(430,160,575,160);ar(1025,160,1160,160);box(10,390,420,150,'Optional model service',['Proposed facts only','Backend credentials']);box(575,390,450,150,'Persistent records',['SQLite local profile','Sources, results, deliveries']);box(1160,390,420,150,'Versioned knowledge',['Rules and catalogues','Applicable evidence']);dr.line((220,390,220,300,750,300,750,240),fill='#185b45',width=4);dr.text((300,310),'Backend model transport',font=ImageFont.truetype(FONT,23),fill='#185b45');dr.line((800,390,800,240),fill='#185b45',width=4);dr.line((1370,390,1370,240),fill='#185b45',width=4)
 p=OUT/'screenshots'/('diagram-'+name+'.png');im=im.crop((0,50,1600,565)) if name in ['solution','software'] else im;im.save(p);return p

def new(title):
 d=Document();s=d.sections[0];s.page_width=Inches(8.27);s.page_height=Inches(11.69);s.left_margin=s.right_margin=Inches(.65);s.top_margin=s.bottom_margin=Inches(.6)
 for n in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
  st=d.styles[n];st.font.name='Arial';st.font.color.rgb=RGBColor.from_string('18242B')
  for node in list(st.element.iter(qn('w:pBdr'))):node.getparent().remove(node)
 d.styles['Normal'].font.size=Pt(10.5);d.styles['Normal'].paragraph_format.space_after=Pt(7);d.styles['Normal'].paragraph_format.line_spacing=1.05
 d.styles['Title'].font.size=Pt(23);d.styles['Title'].font.color.rgb=RGBColor(0,0,0);d.styles['Heading 1'].font.size=Pt(15);d.styles['Heading 2'].font.size=Pt(12)
 install_styles(d);s.header.paragraphs[0].text='ANUBIS  |  SME EVALUATION';s.header.paragraphs[0].runs[0].font.size=Pt(8)
 f=s.footer.paragraphs[0];f.add_run('2 November 2026  •  Controlled evaluation edition').font.size=Pt(8);f.add_run(' '*8);x=OxmlElement('w:fldSimple');x.set(qn('w:instr'),'PAGE');f._p.append(x)
 d.core_properties.author='Traiano Giuseppe Welcome';d.core_properties.title=title
 return d

def para(d,t,style=None):
 p=d.add_paragraph(style=style);render_inline(p,t.replace(';','.'));return p

def table(d,rows,widths=None):
 t=d.add_table(rows=0,cols=len(rows[0]));t.style='Table Grid';t.autofit=False
 widths=widths or ([1.55,2.7,2.72] if len(rows[0])==3 else [6.97/len(rows[0])]*len(rows[0]))
 for col,w in zip(t.columns,widths):col.width=Inches(w)
 for i,row in enumerate(rows):
  r=t.add_row();r._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
  if i==0:r._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
  for c,v,w in zip(r.cells,row,widths):
   c.width=Inches(w);p=c.paragraphs[0];render_inline(p,str(v).replace(';','.'));p.paragraph_format.space_after=Pt(5);p.paragraph_format.space_before=Pt(5)
   for run in p.runs:run.font.size=Pt(9.5);run.bold=True if i==0 else run.bold
   if i==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'EAF0F5');c._tc.get_or_add_tcPr().append(sh)
 return t

def parse_doc(path,name):
 text=path.read_text();text=text.replace('@page\n','') if name in ['03-technical-architecture','06-software-architecture'] else text;d=new(text.splitlines()[0].lstrip('# '));lines=text.splitlines();i=0;pending=False
 if name=='02-methodology':d.styles['Normal'].paragraph_format.space_after=Pt(5)
 while i<len(lines):
  line=lines[i];i+=1
  if not line:continue
  if line=='@page':
   pending=True;continue
  if pending:
   pending=False
   if line.startswith('## '):
    pp=para(d,re.sub(r'[^\w ]','',line[3:]),'Heading 1');pp.paragraph_format.page_break_before=True;continue
  if line.startswith('@figure '):d.add_picture(str(diagram(line.split()[1])),width=Inches(6.97));continue
  if line.startswith('@eq '):
   p=para(d,line[4:]);p.runs[0].font.name='Courier New';p.runs[0].font.size=Pt(9);continue
  if line.startswith('|'):
   rows=[line]
   while i<len(lines) and lines[i].startswith('|'):rows.append(lines[i]);i+=1
   table(d,[[c.strip() for c in r.strip('|').split('|')] for r in rows]);continue
  if line.startswith('### '):para(d,re.sub(r'[^\w ]','',line[4:]),'Heading 2')
  elif line.startswith('## '):para(d,re.sub(r'[^\w ]','',line[3:]),'Heading 1')
  elif line.startswith('# '):para(d,re.sub(r'[^\w ]','',line[2:]),'Title')
  else:para(d,line)
 d.save(DOC/(name+'.docx'))

# Update the methodology baseline while preserving the original edition.
s=(ROOT/'docs/anubis-framework-v2.txt').read_text().replace('Version 2.0 | Draft for review | 1 November 2026','Version 2.1 | SME evaluation edition | 2 November 2026')
s=s.replace('The implementation snapshot reviewed for this paper is the local repository as inspected on 1 November 2026','The implementation snapshot reviewed for this edition is the local repository as inspected on 2 November 2026')
s=s.replace('Online reference pages were checked on 1 November 2026.','References retain the 1 November baseline. The ITU, MLPerf Inference and DeepSeek API pages were rechecked on 2 November 2026. Other mutable references must be rechecked before evidence activation.')
s=s.replace('Version 2.0 makes analytical planning','Version 2.0 introduced analytical planning')
insert='''## Current implementation update for the SME edition
Version 2.1 retains the Version 2.0 numerical methodology and adds the current interpretation and engagement lifecycle. It is an implementation alignment update, not a new performance calibration. The author is Traiano Giuseppe Welcome, traiano@gmail.com.

Optional Copilot now produces a structured fact ledger. Original source statements, quantities, periods, placement and reported or assumed status are retained. Deterministic code converts rates and selects clarification requirements. Human acceptance precedes compilation. A complete interpretation is distinct from partial fact recovery. An LLM is not required for manual operation.

The normal route now proceeds from accepted facts to calculation, then design handoff and immutable delivery. When no valid handoff exists, report-only closure preserves the current evidence, gaps and next measurements. Reopening preserves prior deliveries and allows a new consultation. These lifecycle changes improve traceability without changing the meaning of the sizing equations.

The current local suite passes 13 command groups, including six browser journeys. The SME pack adds a clean-directory installation check and independent arithmetic checks. Earlier live interpretation evaluation passed 45 of 48 original-story trials and 32 of 32 paraphrases. The original-story threshold remained unmet. No production performance or completed human benefit qualification follows from these results.

The exact source snapshot, fresh execution logs, guide walkthrough and independent expected values accompany this edition in documents 07 and 08 and the evidence directory. The original worked example below remains historical and is explicitly identified as such. New guide scenarios have their own current output records.
@page
'''
s=s.replace('## 2 Method and authority boundaries',insert+'## 2 Method and authority boundaries')
(SRC/'02-methodology.txt').write_text(s)

# Preserve the original sixteen identities and stories. Add measurable acceptance and refinement criteria.
scenarios=json.loads((ROOT/'tests/fixtures/architecture-scenarios.json').read_text())
criteria=[
 ('100 requests/minute from 6000/hour. Dense8b and 2000/500 token assumptions permit an eight-GPU node-rounded estimate in the guide. Five seconds remains unqualified.','A positive estimate, all three GPU comparisons and a saved handoff after explicit assumptions. Daily demand is not added.'),
 ('40 requests/minute from 2400/hour. Local generation and outside search remain separate. No implied local 4 TB or initial transfer.','Accept dense8b, one call and 2000/500 tokens for a planning result. Confirm the outside corpus is absent from local storage and transfer requirements.'),
 ('Retain typical four and upper twelve calls. Daily 1500 is insufficient to establish busy-period rate.','First request peak demand and envelope selection. A declared 30 requests/minute and twelve-call envelope must become six model calls/second.'),
 ('80000 / (8 × 3600) = 25/9 calls/second at one call/item. The window crosses midnight.','Preserve an eight-hour batch window. After model and token assumptions, calculate a conditional estimate rather than 80000 simultaneous users.'),
 ('180 × 5 = 900 sampled frames/second. Resolution is 1080p. Retention concerns clips, not full continuous storage by default.','Classify streaming visual inference. Request detector throughput and memory. No fabricated text-model GPU count. Report-only closure works.'),
 ('If all 12000 images belong to one four-hour window, rate is 5/6 images/second. Confirm multiple candidates and window frequency first.','Classify image generation despite batch scheduling. Request model, steps and candidate count. No text-token substitution.'),
 ('300000 examples are not 300000 training tokens. Parameter-efficient method is not confirmed.','Classify adaptation, retain 8B base model and monthly cadence. Ask for method and tokenized dataset. Do not apply full-pretraining sizing silently.'),
 ('90 billion tokens / 30 days is a nominal 34722.22 tokens/second before useful-time adjustment. Model size is still required.','Recognise training and external source data. Ask model, checkpoint and ingestion details. Restricted dense training calculation only after applicable assumptions.'),
 ('Separate assistant and 20000-report batch. 18000 staff is population, not active demand. Disabled access supports separate windows.','Preserve two activities and enforceable non-overlap. Ask each demand and token profile. Reuse capacity only under compatible explicit scheduling.'),
 ('Keep agent, retrieval and nightly indexing. 9 TB plus 40 GB/day is a corpus-growth statement, not measured index bytes.','Recognise overlap. Preserve indexing as unresolved supporting work. Do not issue a complete factory candidate that hides local indexing gaps.'),
 ('Visual processing, indexing and editor text queries are distinct, concurrent activities. No demand numbers are supplied.','Ask separate rates and model evidence. A supported text subtotal must not be represented as complete workload coverage.'),
 ('Text planning precedes conditional image work. Different campaigns may overlap. Approval fraction is unknown.','Preserve conditional relationship without assuming one image job per text request or global non-overlap. Request specialist media sizing.'),
 ('All model compute is outside the factory. 900000 daily requests alone supplies no peak. Local data and integration remain in scope.','No local model GPU allocation solely because AI is used. Record local supporting requirements and connectivity. Close a scoped report if no local GPU candidate exists.'),
 ('Twenty tenants is not demand. Premium reservations and shared standard service may peak together.','Separate model mix, tenant demand and reservation policies. Do not claim a tenant limit from compute-only workload-copy counts.'),
 ('5000 employees is population. Compute location, pattern, model and demand remain unknown.','Ask representative tasks and placement. No invented rate, model or GPU count. Save a final status report if discovery must pause.'),
 ('Fluid simulation is outside text, media-generation and training estimators. Mesh and solver timing must remain in native terms.','Classify other GPU application. Request solver-specific throughput, memory and deadline. Permit closure without a projection and preserve the evidence.')]
text='''# Sixteen business scenarios and acceptance criteria
SME evaluation edition 1.0 | 2 November 2026

## How to use this catalogue
These are fictional but plausible customer engagements. IDs and customer stories preserve the established sixteen-scenario set. Success means correct characterization, justified calculations where supported, and honest closure where unsupported. It does not mean that all sixteen stories must produce GPU numbers without further evidence.

Run each scenario from a fresh engagement. Record the interpreted pattern, placement, original statement, normalized demand, missing inputs, acceptance decision, result status and closure outcome. For Copilot, repeat with a paraphrase and a correction. Compare against these criteria, not exact wording. Do not give the model the expected answer as part of the customer description.

The existing deterministic characterization suite intentionally leaves numerical inputs unresolved for the all-scenario boundary check. It is not sixteen completed procurement designs. Separate interpreted-fact tests and selected end-to-end workflows exercise numerical refinement. Detailed run status appears in document 07.

## Common pass criteria
Every scenario preserves source facts and units, labels assumptions, distinguishes missing from zero, avoids double counting, and leaves accepted facts unchanged until review. A completed sizing case has B300/B200/H200 comparisons where applicable, a traceable projection and a saved completion. A blocked or specialist case has a final report and a retrievable closure record.

The numerical supplements below are explicit test assumptions. They are not measurements claimed by the customer story. Specialist cases pass by identifying the required evidence and refusing an inapplicable estimator.
@page
'''
for i,(a,(expected,success)) in enumerate(zip(scenarios,criteria)):
 text+=f"## {a['id']} {a['name']}\n{a['story']}\n\n"
 text+=f"Expected characterization: {', '.join(a['expected_patterns']) or 'other GPU application'}. {a['expected_arrangement']}\n\n"
 text+=f"Numerical interpretation and scope: {expected}\n\nSuccess criteria: {success}\n\nNegative check: {a['acceptance'].replace(';','.')}\n\nNext measurement: {a['measurement_next']}\n\n"
 if i%2==1 and i<15:text+='@page\n'
(SRC/'04-scenarios.txt').write_text(text)
(OUT/'evidence/scenario-acceptance.json').write_text(json.dumps([dict(a,validation_expected=criteria[i][0],success_criteria=criteria[i][1]) for i,a in enumerate(scenarios)],indent=2))

for n in ['01-business','02-methodology','03-technical-architecture','04-scenarios','06-software-architecture','07-validation','08-deterministic-validation']:
 if (SRC/(n+'.txt')).exists():parse_doc(SRC/(n+'.txt'),n)

# A shared register drives the input tables and collection appendix.
register=[
 ('A01','Customer workload name','Bracken Engineering SME','Explicit fictional name','Consultant. Use a name that the architect and customer recognize. This is an identifier, not sizing demand.'),
 ('A02','Data classification','Public — permitted for direct provider processing','Explicit for fictional data','Data owner. Use Public only for information approved for the chosen endpoint. Real corporate data requires an approved corporate profile.'),
 ('A03','Application and compute','Document assistant. Local answer model','Customer statement','Application owner. Walk through one request and identify the component that executes the answer model.'),
 ('A04','Search and corpus placement','Outside this AI Factory. 4 TB source corpus','Customer statement','Search owner. Confirm the hosting boundary and logical corpus inventory. Index footprint, local copy and transfer volume are separate measurements.'),
 ('A05','Busy-period questions','2400 in one hour → 40 requests/minute','Customer statement and derived rate','Gateway owner. Count successful plus relevant attempted requests in the busiest representative hour. Group timestamps into one-minute bins to refine the peak.'),
 ('A06','Model preset','dense8b','Explicit assumption','Application owner. Inspect the actual model revision and precision. Use the generic preset only as a labelled planning assumption.'),
 ('A07','Input and output tokens per call','2000 input. 500 output','Explicit assumptions','Serving owner. Tokenize complete prompts including retrieved passages and history. Obtain output token counts from serving logs. Sample a representative busy window.'),
 ('A08','Model calls per question','1','Explicit assumption','Application developer. Trace one business transaction through retries and local model invocations. Do not count outside search as another generation call.'),
 ('A09','Factory users and overlap','One organisation. Single activity','Statement and retained single-activity policy','Business owner. Confirm organizational sharing. With one activity, overlap selection does not change its allocation.'),
 ('A10','Local retention and initial transfer','Unspecified. No corpus copy requested','Deliberately unresolved','Storage and migration owners. Obtain actual local inventory and transfer plan. Do not derive these from the outside 4 TB corpus. Unknown is not zero.'),
 ('A11','Network measurements and latency','Unspecified. Dedicated storage policy retained','Deliberately unresolved','Network owner. Supply transfer volume/window, directional bulk flows, RTT objective and storage throughput before a complete network design.'),
 ('A12','Completion notes','Planning requirements issued for SME architecture review. Storage and transfer measurements remain open.','Explicit delivery record','Consultant. Record what was delivered and which measurements remain open. Check the delivery confirmation only after reviewing the selected result.'),
 ('M01','Customer workload name','Alder Contact Services SME','Explicit fictional name','Consultant. Identify the customer and classifier use case.'),
 ('M02','Application pattern and component','Direct model service. Message classification','Explicit selection','Application owner. Confirm that classification is one local text-model call without retrieval or tool loops.'),
 ('M03','Factory users and arrangement','One organisation. Yes — overlapping demand. In this factory. Reserve dedicated capacity unchecked','Retained and selected settings','Service owner. Confirm placement and schedule. Dedicated reservation is unnecessary for this single component but must be reviewed for multi-component work.'),
 ('M04','Describe demand using','Requests per minute. 100','Derived from 6000 busiest-hour messages','Gateway owner. 6000 / 60 = 100. Preserve 45000 daily messages as context, not an extra rate or concurrent-user count.'),
 ('M05','Model preset and calls','dense8b. 1 call per request','Explicit planning assumptions','Application developer. Verify model revision and complete transaction traces. Substitute measurements when available.'),
 ('M06','Input and output tokens per call','2000 and 500','Explicit planning assumptions','Serving owner. Sample full input and response token counts using the selected model tokenizer or request-usage metrics.'),
 ('M07','Response target in seconds','5','Customer service target','Service owner. Define p95 end-to-end response criteria, then load test. This number is retained but not certified by the analytical planner.'),
 ('M08','Locally retained data in TB','2','Fictional planning assumption','Storage owner. Measure logical retained bytes with storage inventory or object-store metrics. Divide decimal bytes by 10^12. Exclude outside data and avoid duplicate shared corpora.'),
 ('M09','Daily growth and horizon','10 GB/day. 365 days','Fictional planning assumptions','Storage owner. Compare daily logical inventories, subtract deletions and apply retention policy. Confirm that growth is net retained growth.'),
 ('M10','Initial dataset and loading window','2 TB. 8 hours','Fictional migration plan','Migration owner. Record bytes that must cross the customer connection and the allowed duration. Use actual transferred volume if compression changes it.'),
 ('M11','Ongoing incoming and outgoing data','10 GB/day in. 1 GB/day out','Fictional planning assumptions','Network owner. Read directional interface or application transfer counters over 24 hours. Exclude request/response traffic already modelled from tokens.'),
 ('M12','Usable link fraction and loading overlap','0.7. Yes — add the demands','Retained planning defaults','Network architect. Establish usable capacity from contention and protocol overhead. Confirm whether loading and normal operation coincide.'),
 ('M13','Customer datacenter round-trip target','20 ms','Fictional requirement','Service owner sets target. Network engineer measures representative RTT with ping or an application probe. Do not substitute model response time.'),
 ('M14','Aggregate storage reads and writes','4 Gbps reads. 2 Gbps writes','Fictional directional payload assumptions','Storage engineer. Use aggregate client or array byte counters and peak windows. Convert bytes/second × 8 / 10^9. Include coincident checkpoint and ingestion writes.'),
 ('M15','East-west payload per GPU','Blank','Unresolved','Distributed runtime owner. Obtain collective communication telemetry under the intended parallel strategy. A fabric choice alone does not supply workload bandwidth.'),
 ('M16','Customer context and measurement notes','Fictional scenario. Busy hour 6000/60. Token and infrastructure assumptions. Five seconds is not certified.','Explicit explanatory note','Consultant. Preserve provenance, observation window and uncertainty. Free text does not override typed fields.'),
 ('M17','Completion notes','Manual planning scenario delivered for SME review.','Explicit delivery record','Consultant. Review the selected projection before confirming delivery.'),
 ('D01','Infrastructure deployment profile','HGX B300. Spectrum-X. Enterprise reference design with two network planes','Default profile','Architect. The internal ID SX-HGXB300-DP-ENT-1.0.0 means Spectrum-X, HGX B300, dual plane, Enterprise, version 1.0.0. It is not a workload name or universal NCP minimum.'),
 ('D02','Sensitivity envelope','±30 percent','Accepted default','Consultant. Select 10, 20 or 30 percent for throughput sensitivity. These are not confidence intervals or arithmetic tolerances.'),
 ('D03','Compute and memory efficiency','0.35 compute. 0.50 memory bandwidth','Versioned defaults','Performance engineer. Calibrate against representative serving measurements before qualification. Do not apply the factor twice to already effective throughput.'),
 ('D04','Serving allocation','1 GPU per replica. 32 concurrent sequences. 8192 context tokens','Versioned defaults','Runtime owner. Inspect deployment and scheduler settings. Concurrency here is active model sequences, not all customer employees.'),
 ('D05','Weight and KV bytes and workspace','2 bytes per weight. 2 per KV value. 8 GB workspace','Versioned defaults','Model/runtime owner. Confirm precision, cache representation and peak workspace from runtime memory telemetry.'),
 ('D06','Host provisions per GPU','256 GB RAM. 3840 GB local disk. 16 CPU cores','Versioned defaults','Server architect. Compare with actual node configuration and measured preprocessing, cache and orchestration demand. These are provisions, not measured minimums.'),
 ('D07','Storage free space and protocol','20 percent free space. Protocol multiplier 1.2. Four bytes/token','Versioned defaults','Storage/network architect. Check free-space policy, wire overhead and real serialized request sizes. Include image/tool payloads separately.'),
 ('D08','Service fraction and expansion lead time','1.0. No accepted capacity shortfall. 90 days','Versioned defaults','Business owner and procurement. Confirm expansion lead time and required service. Reduced service requires explicit approval, never silent rounding down.'),
 ('D09','Training-only defaults','16 bytes/parameter state. 32 GB activation/GPU','Not active in these inference scenarios','Training engineer. Review optimizer, sharding and activation behaviour for training. These defaults do not affect the two inference examples.'),
 ('D10','Handoff selections','Intended candidate planning:factory. HGX_B300. Spectrum-X. Project name retained','Default compatible mapping','Architect. Confirm intended versus modelled platform. Preserve companion requirements and approve substitutions explicitly when needed.')]
(OUT/'evidence/playbook-input-register.json').write_text(json.dumps(register,indent=2))

def guide():
 d=new('Anubis technical user guide');d.styles['Normal'].paragraph_format.space_after=Pt(5);sec=d.sections[0];sec.page_width=Inches(11.69);sec.page_height=Inches(8.27)
 para(d,'Anubis technical user guide','Title');para(d,'Install, configure and complete assisted and manual engagements','Subtitle')
 para(d,'This guide takes a consultant from first installation to saved design requirements. Follow the assisted Bracken example or the fully manual Alder example. Both routes use the same deterministic sizing engine. A successful engagement ends with retrievable deliverables, not just a calculation on screen.')
 para(d,'Reading this guide: [[field:Field label]] = [[value:Value to enter or select]]. [[control:Button or expandable section]]. [[state:Unchecked or blank]] is a setting. Ordinary text explains the action.')
 d.add_picture(str(diagram('method')),width=Inches(10.2))
 para(d,'The four engagement stages surround the guided editor. Inside the builder, Choose application → Confirm arrangement → Describe scale → Review and estimate are intake substeps. Architecture maps locate the measurements and scope boundaries.')
 d.add_page_break();para(d,'Install the local application','Heading 1')
 para(d,'Start from the reference-source folder in this archive or an authorized Anubis checkout. On macOS, install Apple Command Line Tools with xcode-select --install if absent. If Homebrew is not installed, follow https://docs.brew.sh/Installation . Then run brew install cmake node openssl@3 sqlite python. These are prerequisite setup instructions. The recorded qualification used the toolchain versions in evidence/environment.json.')
 para(d,'Use an authorized source checkout with CMake 3.24 or later, a C++20 compiler supporting int128, OpenSSL and SQLite development libraries, Node/npm and Python 3. The evaluated host is macOS arm64. The observed toolchain and pinned dependencies are included in evidence. A fresh operating-system or Windows installation has not been qualified.')
 table(d,[['Step','Action or command','Expected result'],['I1','Open a terminal in the authorized Anubis repository. Check cmake --version, c++ --version, node --version, npm --version and python3 --version.','Resolve missing tools using the prerequisite commands above. Compare with evidence/environment.json.'],['I2','cmake --preset local','CMake finds OpenSSL, SQLite and threads and generates build files. If needed, run CMAKE_PREFIX_PATH="$(brew --prefix openssl@3):$(brew --prefix sqlite)" cmake --preset local.'],['I3','cmake --build --preset local -j4','The build/anubis executable and test drivers are produced.'],['I4','npm ci --ignore-scripts\nnpm run build','Locked development dependencies and ui/dist are created. Keep the docs directory because help files are build inputs.'],['I5','ctest --test-dir build --output-on-failure','Both core and characterization test executables pass.'],['I6','python3 deploy/local/run.py','The local service starts. Leave this terminal running. Open http://127.0.0.1:8787 in a browser.']], [.5,5.3,4.5])
 para(d,'Commands are terminal instructions, not screenshots of a terminal session. Fresh-directory execution logs are supplied in evidence. A checkout may need an authorized repository download. No public repository address is implied.')
 d.add_page_break();para(d,'Get your access token','Heading 1')
 para(d,'On first launch, the application creates [[value:.anubis/identities.json]] in the repository. Open that private file locally in a text editor. Copy the [[field:token]] value for your identity, without quotation marks. Enter it in [[field:Access token]] and click [[control:Open workspace]]. There is no default public password.')
 para(d,'On macOS, hidden files can be shown in Finder with Command Shift Period. The .anubis folder is hidden by convention. Keep the identity file private. Anubis access tokens authenticate to Anubis. Provider API keys pay for and authorize model-service calls. They are different credentials.')
 steps=[('L1','Open the local URL. Fill [[field:Access token]] with your private identity token. Click [[control:Open workspace]]. The screenshot intentionally shows an empty field.','01-login-crop')]
 step_table(d,steps)
 d.add_page_break();para(d,'Configure the Agentic Copilot','Heading 1')
 para(d,'An administrator configures the connection once. The manual route needs no provider. The following profile was exercised with fictional public data. Use the model approved and available in your own account. A chat-product subscription must not be assumed to include API access.')
 table(d,[['ID','Field or action','Exact example and basis'],['C01','Protected backend key','Put your actual key in the private .env file as DEEPSEEK_API_KEY=YOUR_SECRET. Do not use the literal placeholder. Do not commit this file or put the key in the UI.'],['C02','Restart local service','Stop the existing local process with Ctrl C, then run python3 deploy/local/run.py. This loads the backend credential.'],['C03','Connection name / Provider','DeepSeek SME review / deepseek'],['C04','Origin / API path','https://api.deepseek.com / /chat/completions'],['C05','Model identifier / reasoning','deepseek-flash / low. This is the tested example, not a guarantee of future provider availability.'],['C06','Backend secret environment variable','ANUBIS_AI_KEY_DEEPSEEK. Enter the name only. The launcher maps DEEPSEEK_API_KEY to this name.'],['C07','Approved to process corporate data','Unchecked for these fictional public examples. Approval must reflect your actual provider agreement.'],['C08','Approved MCP tools JSON','Retain []. No MCP server is needed for a direct provider.']], [.5,3,6.8])
 d.add_page_break();step_table(d,[('C1','Click [[control:AI connections]]. Set all profile fields from C03–C08. Choose [[field:DeepSeek reasoning effort]] = [[value:low]]. Click [[control:Save connection]].','03-connection-form')])
 d.add_page_break();step_table(d,[('C2','Click [[control:Test DeepSeek SME review]]. Wait for the test job to finish successfully. A successful capability test verifies structured transport, not general interpretation quality. If it fails, correct the configuration or funding before continuing.','04-connection-tested')])
 para(d,'For another public provider, select its adapter and approved model. Nonstandard corporate origins require the backend ANUBIS_AI_ALLOWED_ORIGINS setting. MCP tool discovery and model inference are separate capabilities. See document 03 and the included copilot-operation.txt for the exact supported MCP contract.')
 # Two playbooks. Register immediately follows introduction.
 for prefix,title,intro in [('A','Bracken Engineering assisted playbook','Engineers ask a local answer model questions about maintenance manuals. An existing search service outside this AI Factory indexes a 4 TB corpus and returns passages. The busiest hour contains 2400 questions. The first estimate explicitly assumes dense8b, one call per question, 2000 input tokens and 500 output tokens. The corpus is not copied locally.'),('M','Alder Contact Services manual playbook','A regional service desk classifies 45000 incoming messages daily. The busiest hour receives 6000 messages. Classification is one local text-model call. The response target is five seconds. For this planning exercise, use dense8b and explicit data and network assumptions listed below. This route uses no Copilot.')]:
  d.add_page_break();para(d,title,'Heading 1');para(d,intro)
  rows=[['ID','Workflow field','Value or action','Basis']]+[[r[0],'[[field:'+r[1]+']]','[[value:'+r[2]+']]',r[3]] for r in register if r[0].startswith(prefix)]
  rt=table(d,rows,[.5,2.5,5.1,2.2])
  for row in rt.rows:
   for cell in row.cells:
    for pp in cell.paragraphs:pp.paragraph_format.space_before=Pt(2);pp.paragraph_format.space_after=Pt(2)
  para(d,'The shared defaults D01–D10 below also apply. Each register ID has a parameter-collection explanation in the appendix. Blank fields are deliberately unresolved.')
  if prefix=='A':
   d.add_page_break();para(d,'Locate the assisted measurements','Heading 1');d.add_picture(str(diagram('application')),width=Inches(10.2));para(d,'Measure request volume at the application entry, complete tokens at the model call, and data inventory at the system actually retaining the data. Outside this AI Factory can be a customer search cluster or a managed search service. It does not mean a particular storage product or necessarily public Internet.')
   story=json.loads((OUT/'evidence/gui-walkthrough.json').read_text())['story'];para(d,'Customer description to enter','Heading 2');para(d,story)
   steps=[('A1','Click [[control:Consultant Copilot]]. Set [[field:Customer workload name]] = [[value:Bracken Engineering SME]]. Set [[field:Data classification]] = [[value:Public — permitted for direct provider processing]]. Click [[control:Start assisted engagement]].','05-assisted-start'),('A2','Select [[field:Model connection]] = [[value:DeepSeek SME review]]. Paste the customer description into [[field:What should we know about the workload?]]. Click [[control:Ask copilot]].','06-description'),('A3','The active status and elapsed time show that work is in progress. Wait for the proposal. Use Cancel only if you intend to stop publication. Provider response time can vary.','07-working'),('A4','Read the proposed facts and their source statements. Confirm local answer compute, outside search, 2400 questions/hour, one call, dense8b and 2000/500 tokens. Wording and component names may vary with the model. Correct discrepancies before accepting.','08-proposal'),('A5','Review the complete proposal. Check [[field:I reviewed the selected values and accept the planning assumptions.]]. Click [[control:Apply selected]]. The human decision is what changes accepted inputs.','09-review'),('A6','In [[control:Your next step]], click [[control:Review and calculate GPU estimate]]. The accepted rate should be 40 requests/minute. Missing local storage and transfer measurements remain unresolved.','10-accepted'),('A7','Review the deployment profile and ±30 percent sensitivity. Expand [[control:Inspect versioned planning defaults]] if needed. Check [[field:Use these planning assumptions]]. Click [[control:Calculate estimate]].','11-review-estimate'),('A8','Scroll to [[control:GPU workload comparison]]. Read eight GPUs for B300, B200 and H200. The 256-GPU default factory anchor is a separate deployment selection. All estimates remain conditional.','12-assisted-gpu-comparison'),('A9','Click [[control:Continue to Design handoff]] at the top of analysis. Review [[field:Design project name]], intended candidate, platform and fabric. Retain the compatible defaults D10. Click [[control:Prepare projection]].','13-handoff'),('A10','Read [[control:AI Factory design executive summary]]. Review missing network measurements and the mapping ledger. Download the executive summary, design intake and companion specification using the visible download controls. Preserve them together.','14-summary-crop'),('A10b','Review the network roles, tenancy qualification and architect actions. Use the download controls below the executive summary and mapping ledger. Storage and transfer gaps remain visible.','14-summary-networks'),('A11','Set [[field:Completion notes]] to A12. Check [[field:I confirm that these selected requirements are delivered.]]. Click [[control:Complete engagement]]. Completion records delivery of conditional requirements, not physical performance approval.','15-complete'),('A12','Confirm [[control:Saved deliverables]]. Use [[control:Download complete engagement record]] to retrieve the immutable delivery. Reopening for revisions preserves this version.','16-saved'),('A13','Click [[control:Cases]]. Confirm [[state:Completed · requirements delivered]]. Click [[control:View engagement]] to retrieve it later. A historical Copilot page is not an unfinished conversation.','17-cases')]
  else:
   steps=[('M1','Click [[control:New engagement]]. Set [[field:Customer workload name]] = [[value:Alder Contact Services SME]]. Click [[control:Add Direct model service]], then [[control:Continue]].','18-manual-pattern'),('M2','Retain [[field:Factory users]] = [[value:One organisation]]. Select [[field:Do activities run at the same time?]] = [[value:Yes — overlapping demand]]. Set [[field:Component name 1]] = [[value:Message classification]]. Retain local compute and unchecked dedicated reservation. Click [[control:Continue]].','19-manual-arrangement'),('M3','Retain [[field:Model preset]] = [[value:dense8b]] and [[field:Describe demand using]] = [[value:Requests per minute]]. Enter [[field:Peak requests per minute]] = [[value:100]], calls = [[value:1]], input tokens = [[value:2000]] and output tokens = [[value:500]].','20-manual-scale'),('M4','Expand [[control:Optional service target]]. Enter [[field:Response target in seconds]] = [[value:5]]. Expand [[control:Data capacity and growth]]. Set retained data = [[value:2 TB]], growth = [[value:10 GB/day]] and horizon = [[value:365 days]].','21-manual-data'),('M5','Expand [[control:Factory networks and customer datacenter connection]]. Set initial dataset = [[value:2 TB]], loading window = [[value:8 hours]], ongoing incoming = [[value:10 GB/day]], outgoing = [[value:1 GB/day]], usable fraction = [[value:0.7]] and RTT target = [[value:20 ms]].','22-manual-network'),('M6','Set [[field:Aggregate storage reads in Gbps]] = [[value:4]] and writes = [[value:2]]. Leave [[field:East-west payload per GPU in Gbps]] [[state:blank]]. Retain overlapping loading. Enter M16 in the notes. Click [[control:Continue]].','23-manual-storage-network'),('M7','Review the default deployment profile and ±30 percent sensitivity. Check [[field:Use these planning assumptions]], then click [[control:Calculate estimate]].','24-manual-review'),('M8','Inspect GPU comparisons and the deployment recommendation. Expect eight workload GPUs on each supported alternative and a 256-GPU default profile anchor. Inspect retained usable capacity of 7.0625 TB and the four network roles.','25-manual-gpu-comparison'),('M9','Click [[control:Continue to Design handoff]], then [[control:Prepare projection]]. Read the executive summary. The companion specification carries resource details that do not fit the fixed downstream intake. Download the deliverables.','26-manual-summary'),('M10','Enter M17 in [[field:Completion notes]], confirm delivery and click [[control:Complete engagement]]. Confirm [[control:Saved deliverables]]. Return through Cases to retrieve or reopen the engagement.','27-manual-saved')]
  for st in steps:d.add_page_break();para(d,title,'Heading 1');step_table(d,[st])
  para(d,'Checkpoint: the resulting workload GPU count is eight. Each GPU requires approximately 58.359738 GB in the selected memory model. A 256-GPU anchor supports 32 equivalent compute allocations under these assumptions. This is not a tenant-count guarantee. Model latency, storage realization and remaining network gaps require architectural review.')
 d.add_page_break();para(d,'Shared planning and handoff defaults','Heading 1');table(d,[['ID','Field','Value','Basis']]+[[r[0],r[1],r[2],r[3]] for r in register if r[0].startswith('D')],[.5,2.5,5.1,2.2])
 para(d,'The compiled hardware catalogue additionally supplies GPU memory, bandwidth, dense compute, usable HBM fraction and node host configuration. These are frozen in evidence/planning-catalog.json and the result JSON. They are not hidden customer measurements. Model dimensions and all effective planning assumptions are retained in the normalized workload and result.')
 d.add_page_break();para(d,'Conclude an engagement without a handoff','Heading 1')
 para(d,'If the workload is unsupported or essential numbers remain unknown, do not invent measurements to reach stage 4. Open Design handoff and choose Review final status report. Read the preserved facts, unresolved requirements and next measurements. Supply a closure reason and confirm the report-only closure. The case should show Closed · final status report. Saved reports can be retrieved and the engagement reopened when evidence becomes available.')
 para(d,'If a result is stale after editing, return to calculation and create a new result. If an advanced edit conflicts with Copilot, review the conflicting fields or create a separate assisted copy. Opening the advanced editor alone should not disable assistance. Use Trash only for recoverable deletion, not as a substitute for formal completion.')
 para(d,'Troubleshooting','Heading 2');table(d,[['Symptom','Action','Meaning'],['Login fails','Use the token for your private identity and verify the service root. Restart after identity changes.','Provider keys do not authenticate to Anubis.'],['Corporate data rejected by profile','Use an approved corporate connection or classify only genuinely public data as Public.','This is a deliberate data-policy boundary.'],['Model unavailable or account unfunded','Check provider status, API billing and the saved profile. Test again, then retry explicitly.','Do not expect silent fallback. Manual intake remains available.'],['GPU comparison missing','Check pattern, compute location, model, demand and accepted assumptions.','Specialist or incomplete workloads may correctly lack a candidate.'],['Network rate missing','Supply actual transfer or directional I/O measurements.','Storage TB and fabric choice cannot supply all bandwidth requirements.'],['Saved case appears open','Open means no completed delivery or formal report closure has been recorded.','Reading a result is not a completion action.']], [2.3,4.5,3.5])
 d.add_page_break();para(d,'Appendix Parameter collection guide','Heading 1');para(d,'Each entry below corresponds to the input register. For unknown values, retain blank or unknown and record the responsible owner. Do not copy planning assumptions into a measured-data field. Capture source date, units, scope and observation interval when refining a value.')
 for r in register:
  para(d,r[0]+' '+r[1],'Heading 2');para(d,r[4])
 para(d,'Connection settings C01 to C08','Heading 2');para(d,'The administrator obtains the API credential and approved model from the provider account, stores the secret privately, and checks the exact API origin and path against provider documentation. Verify data approval with the organization responsible for the information. C01 and C02 are protected deployment operations. C03 through C08 are profile metadata and must not contain a secret value. The UI defaults to 20 turns and 8192 output tokens for a saved profile. Review budgets before live use.')
 para(d,'Practical measurement methods','Heading 2');para(d,'For request rates, export gateway timestamps as CSV and group by minute. Report the busiest representative hour and its minute distribution. For token counts, use the deployed model tokenizer on complete prompts and responses or export API usage counters. For agent expansion, correlate all model spans by business transaction ID and count typical and upper calls including retries. For storage, compare logical inventories over time and separately measure read/write byte counters. For transfer throughput, divide observed transferred bytes by elapsed seconds and convert bytes to bits when reporting Gbps. For latency, retain a distribution and its endpoints rather than a single unexplained average.')
 para(d,'Useful primary references','Heading 2');para(d,'OpenTelemetry metrics overview: https://opentelemetry.io/docs/concepts/signals/metrics/ . NVIDIA DCGM exporter: https://docs.nvidia.com/datacenter/cloud-native/gpu-telemetry/latest/dcgm-exporter.html . Prometheus query functions: https://prometheus.io/docs/prometheus/latest/querying/functions/ . DeepSeek API contract: https://api-docs.deepseek.com/api/create-chat-completion/ . These are measurement aids and interface references, not proof that a metric is automatically collected by Anubis.')
 para(d,'Outside this AI Factory','Heading 2');para(d,'Compute examples include a customer GPU cluster, another private inference platform or a managed model endpoint. Search examples include a customer Elasticsearch or OpenSearch cluster and a managed cloud search service. Source documents might reside in object storage, an enterprise file share, NAS, a document-management platform or a database. A source corpus and search index can use different platforms. Outside describes the boundary of the factory being sized, not geography, protocol or a storage tier. The external customer connection is the path crossing that boundary. Local copies and initial transfers require separate explicit values.')
 d.save(DOC/'05-technical-user-guide.docx')

def step_table(d,steps):
 for num,activity,screen in steps:
  t=table(d,[['Step','Activity and values','Screen reference'],[num,activity,'']],[.45,3.25,6.6]);c=t.rows[1].cells[2];p=c.paragraphs[0];p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0)
  path=OUT/'screenshots'/(screen+'.png');im=Image.open(path);width=6.4;height=width*im.height/im.width
  if height>4.85:width=4.85*im.width/im.height
  p.add_run().add_picture(str(path),width=Inches(width));c.add_paragraph(screen+'.png').runs[0].font.size=Pt(7)

guide()
print('Built documents:',len(list(DOC.glob('*.docx'))))
