"""Shared semantic Word typography. Use explicit markup for new instructions.

[[field:Exact UI label]], [[value:Exact value]], [[control:Button]],
[[state:Unchecked]]. Legacy phrases are migrated by a bounded vocabulary.
"""
import re
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import RGBColor

STYLES = {
 'field': ('Anubis UI Field', 'Arial', '17365D', True, False),
 'value': ('Anubis UI Value', 'Courier New', '185B45', False, False),
 'control': ('Anubis UI Control', 'Arial', '17365D', True, False),
 'state': ('Anubis UI State', 'Arial', '185B45', True, True),
}
FIELDS = '''Customer workload name|Factory users|Do activities run at the same time?|Component name 1|Compute location 1|Reserve dedicated capacity 1|Search and indexing location 1|Model preset|Describe demand using|Peak requests per minute|Model calls per request or job|Input tokens per model call|Output tokens per model call|Response target in seconds|Locally retained data in TB|Daily growth in GB|Planning horizon in days|Customer context and measurement notes|Sensitivity envelope|Design project name|Intended candidate|Design modelling platform|Modelling fabric choice|Infrastructure deployment profile|Access token'''.split('|')
CONTROLS = '''New engagement|Add Document or search assistant|Add Direct model service|Continue|Optional service target|Data capacity and growth|Factory networks and customer datacenter connection|Inspect versioned planning defaults|Use these planning assumptions|Calculate estimate|Design handoff|Prepare projection|Download design intake|Download readable architecture brief|Download companion specification|Open workspace|Workload builder|Clear unsaved intake|Open advanced workload editor'''.split('|')
PAIRS = {
 'Customer workload name':['Bracken Engineering','Alder Contact Services'],
 'Factory users':['One organisation'],
 'Do activities run at the same time?':['Yes — overlapping demand'],
 'Component name 1':['Manual assistant','Message classification'],
 'Compute location 1':['In this factory'],
 'Search and indexing location 1':['Existing service outside this AI Factory'],
 'Model preset':['dense8b'], 'Describe demand using':['Requests per minute'],
 'Peak requests per minute':['40','100'], 'Model calls per request or job':['1'],
 'Response target in seconds':['5'], 'Sensitivity envelope':['±30%'],
 'Design project name':['Bracken Engineering','Alder Contact Services'],
 'Intended candidate':['planning:factory'], 'Design modelling platform':['HGX_B300'],
 'Modelling fabric choice':['Spectrum-X'],
 'Infrastructure deployment profile':['HGX_B300 · Spectrum-X · Enterprise RA dual plane'],
}

def install_styles(doc):
 for _, (name,font,color,bold,italic) in STYLES.items():
  s=doc.styles[name] if name in doc.styles else doc.styles.add_style(name,WD_STYLE_TYPE.CHARACTER)
  s.font.name=font;s.font.color.rgb=RGBColor.from_string(color)
  s.font.bold=bold;s.font.italic=italic

def markup_legacy(text):
 text=text.replace('Retain usable link fraction 0.7 and initial-loading overlap Yes.', 'Retain [[field:Usable link fraction]] = [[value:0.7]] and [[field:Does initial loading overlap normal operation?]] = [[value:Yes — add the demands]].')
 # Exact field/value pairs only. Never infer values from sentence punctuation.
 for field,values in PAIRS.items():
  for value in values:
   text=text.replace(field+' = '+value, f'[[field:{field}]] = [[value:{value}]]')
 parts=re.split(r'(\[\[\w+:.*?\]\])',text)
 vocabulary={**{x:'field' for x in FIELDS},**{x:'control' for x in CONTROLS},'unchecked':'state','blank':'state'}
 pattern=re.compile(r'(?<!\w)('+ '|'.join(re.escape(x) for x in sorted(vocabulary,key=len,reverse=True))+r')(?!\w)')
 for i,p in enumerate(parts):
  if not p.startswith('[['):parts[i]=pattern.sub(lambda m:f'[[{vocabulary[m[0]]}:{m[0]}]]',p)
 return ''.join(parts)

def render_inline(paragraph,text):
 paragraph.clear()
 for part in re.split(r'(\[\[(?:field|value|control|state):.*?\]\])',text):
  m=re.fullmatch(r'\[\[(field|value|control|state):(.*?)\]\]',part)
  if m:
   role,value=m.groups()
   paragraph.add_run('['+value+']' if role=='control' else value,style=STYLES[role][0])
  else:paragraph.add_run(part)

def format_playbook(doc):
 install_styles(doc)
 # Prose with commands, including login instructions. Preserve images, links and code.
 for p in doc.paragraphs:
  if p.style.name not in ('Normal',) or not p.text or p._p.xpath('.//w:drawing | .//w:hyperlink'):continue
  if any(r.font.name=='Courier New' for r in p.runs):continue
  render_inline(p,markup_legacy(p.text))
 for t in doc.tables:
  head=[c.text for c in t.rows[0].cells]
  if head and head[0]=='ID' and 'Workflow field' in head and 'Value or action' in head:
   for row in t.rows[1:]:
    for idx,role in [(head.index('Workflow field'),'field'),(head.index('Value or action'),'value')]:
     for p in row.cells[idx].paragraphs:
      for r in p.runs:r.style=STYLES[role][0]
  if head==['Step','Activity and values','Screen reference']:
   for row in t.rows[1:]:
    cell=row.cells[1];text=cell.text;cell.text=''
    for i,block in enumerate(text.split('\n\n')):
     p=cell.paragraphs[0] if i==0 else cell.add_paragraph()
     render_inline(p,markup_legacy(block))
 # Compact reader key before the scenario, leaving the input register adjacent to it.
 title=next(p for p in doc.paragraphs if p.text=='The customer application')
 p=title.insert_paragraph_before()
 render_inline(p,'Reading this guide: [[field:Field label]] = [[value:Value to select or enter]]. [[control:Button or expandable section]]. [[state:Unchecked / blank]] describes a setting. Other text explains why.')
