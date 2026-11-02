from pathlib import Path
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables/agent-architecture'
OUT.mkdir(exist_ok=True)
def figure(name):
 im=Image.new('RGB',(1600,650),'white');dr=ImageDraw.Draw(im)
 def font(n,b=False):return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if b else '')+'.ttf',n)
 def box(x,y,w,h,lines,fill='#edf3f6'):
  dr.rounded_rectangle((x,y,x+w,y+h),radius=10,outline='#35516a',fill=fill,width=3)
  for j,line in enumerate(lines):
   f=font(26,j==0);bb=dr.textbbox((0,0),line,font=f);dr.text((x+(w-bb[2])/2,y+20+j*36),line,font=f,fill='black')
 def arrow(x,y,xx,yy):
  dr.line((x,y,xx,yy),fill='#35516a',width=4)
  if yy==y:dr.polygon([(xx,yy),(xx-14,yy-9),(xx-14,yy+9)],fill='#35516a')
  else:dr.polygon([(xx,yy),(xx-9,yy-14),(xx+9,yy-14)],fill='#35516a')
 if name=='architecture':
  box(10,30,460,115,['Consultant workspace','Diagram, forms and copilot'])
  box(570,30,460,115,['Agent harness','Context, policy and tool dispatch'])
  box(1140,30,450,115,['Model service','Corporate or direct connection'])
  arrow(470,85,570,85);arrow(1030,85,1140,85)
  box(570,245,460,115,['Application API','Validation, review and revisions'])
  arrow(800,145,800,245)
  box(10,245,460,115,['Approved MCP tools','Scoped knowledge and resources'])
  arrow(470,300,570,300)
  box(1140,245,450,115,['Audit and accepted state','Sources, actions and versions'])
  arrow(1030,300,1140,300)
  box(570,465,460,115,['Deterministic engine','GPU, memory, storage and networks'],'#e8f1e9')
  arrow(800,360,800,465)
  box(1140,465,450,115,['Design handoff','Preview, export or approved send'])
  arrow(1030,520,1140,520)
  dr.text((20,500),'Only accepted revisions',font=font(28,True),fill='black')
  dr.text((20,540),'become calculation inputs',font=font(28),fill='black')
 else:
  box(10,10,1580,75,['Application  >  Arrangement  >  Demand  >  Estimate  >  Design handoff'])
  box(10,110,980,300,['Application architecture','Users  →  Assistant in factory  →  Search outside factory','↓','Document source and data placement','Select a component to locate its measurements'])
  box(10,435,980,195,['Selected component inputs','Peak requests    [12 request/s]    Customer measurement','Input length     [preset]              Planning assumption','Definition   |   Why it matters   |   How to measure'])
  box(1020,110,570,520,['Consultant Copilot','Connected to approved model','', 'One material question at a time','', 'Proposed changes','Field  |  Value  |  Basis','', 'Apply selected    Edit    Discard','', 'Accepted draft and result status'])
 p=OUT/(name+'.png');im.save(p);return p
D=Document();s=D.sections[0];s.page_width=Inches(8.27);s.page_height=Inches(11.69)
s.top_margin=s.bottom_margin=Inches(.65);s.left_margin=s.right_margin=Inches(.7)
for n in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
 st=D.styles[n];st.font.name='Arial';st.font.color.rgb=RGBColor(0,0,0)
D.styles['Normal'].font.size=Pt(10.5);D.styles['Normal'].paragraph_format.space_after=Pt(7);D.styles['Normal'].paragraph_format.line_spacing=1.06
D.styles['Title'].font.size=Pt(25)
for node in list(D.styles.element.iter(qn('w:pBdr'))):node.getparent().remove(node)
D.styles['Heading 1'].font.size=Pt(17)
D.styles['Heading 2'].font.size=Pt(12)
f=s.footer.paragraphs[0];f.add_run('Anubis  |  Agentic AI architecture  |  Version 1.0').font.size=Pt(8)
f.add_run(' '*8);node=OxmlElement('w:fldSimple');node.set(qn('w:instr'),'PAGE');f._p.append(node)
def p(txt,style=None):return D.add_paragraph(txt,style)
lines=(ROOT/'docs/anubis-agent-architecture.txt').read_text().splitlines();i=0
while i<len(lines):
 line=lines[i];i+=1
 if not line:continue
 if line=='@page':D.add_page_break();continue
 if line.startswith('@figure '):
  pic=D.add_picture(str(figure(line.split()[1])),width=Inches(6.87));pic._inline.docPr.set('descr','Logical architecture of controlled agent assistance' if 'architecture' in line else 'Workspace with architecture diagram, workload inputs and optional copilot panel');continue
 if line.startswith('|'):
  rows=[line]
  while i<len(lines) and lines[i].startswith('|'):rows.append(lines[i]);i+=1
  data=[[v.strip() for v in r.strip('|').split('|')] for r in rows];n=len(data[0]);t=D.add_table(rows=0,cols=n);t.autofit=False
  widths=[1.7,5.17] if n==2 else [1.25,2.7,2.92]
  for col,w in zip(t.columns,widths):col.width=Inches(w)
  borders=OxmlElement('w:tblBorders')
  for edge in ['top','left','bottom','right','insideH','insideV']:
   e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
  t._tbl.tblPr.append(borders)
  for j,vals in enumerate(data):
   row=t.add_row();row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
   if j==0:row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
   for cell,txt,w in zip(row.cells,vals,widths):
    cell.width=Inches(w);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
    pr=cell._tc.get_or_add_tcPr();sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'DDE8EF' if j==0 else ('F5F7F9' if j%2==0 else 'FFFFFF'));pr.append(sh)
    marg=OxmlElement('w:tcMar')
    for side in ['top','bottom','left','right']:
     e=OxmlElement('w:'+side);e.set(qn('w:w'),'85');e.set(qn('w:type'),'dxa');marg.append(e)
    pr.append(marg);para=cell.paragraphs[0];para.paragraph_format.space_after=Pt(2);para.paragraph_format.space_before=Pt(2);para.paragraph_format.line_spacing=1.02
    run=para.add_run(txt);run.font.size=Pt(9.5);run.bold=j==0
  p('').paragraph_format.space_after=Pt(0)
 elif line.startswith('### '):p(line[4:],'Heading 2')
 elif line.startswith('## '):p(line[3:],'Heading 1')
 elif line.startswith('# '):p(line[2:],'Title')
 else:p(line)
D.core_properties.title='Anubis Agentic AI Technical Architecture'
D.core_properties.author='Traiano Giuseppe Welcome'
D.core_properties.subject='Implementation of optional agent assistance for deterministic workload sizing'
D.save(OUT/'Anubis_Agentic_AI_Technical_Architecture_v1.docx')
print(OUT/'Anubis_Agentic_AI_Technical_Architecture_v1.docx')
