"""Build the Version 2 methodology without modifying the Version 1 baseline."""
from pathlib import Path
import re,json,hashlib
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables/methodology-v2';OUT.mkdir(exist_ok=True)
source=ROOT/'docs/anubis-framework-v2.txt'

def figure(name):
 im=Image.new('RGB',(1800,480),'white');dr=ImageDraw.Draw(im)
 def font(n,b=False):return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if b else '')+'.ttf',n)
 def box(x,y,w,h,title,detail):
  dr.rounded_rectangle((x,y,x+w,y+h),radius=12,fill='#edf3f6',outline='#34556b',width=3)
  for j,line in enumerate([title]+detail.split('\n')):
   f=font(25,j==0);bb=dr.textbbox((0,0),line,font=f);dr.text((x+(w-bb[2])/2,y+22+j*37),line,font=f,fill='#172e3c')
 def arrow(x,y,xx,yy):
  dr.line((x,y,xx,yy),fill='#34556b',width=4)
  if xx>x:dr.polygon([(xx,yy),(xx-13,yy-9),(xx-13,yy+9)],fill='#34556b')
  else:dr.polygon([(xx,yy),(xx-9,yy-13),(xx+9,yy-13)],fill='#34556b')
 if name=='method':
  labels=[('Describe','Customer intent\nArchitecture patterns'),('Measure','Demand and scope\nExplicit assumptions'),('Estimate','Resource model\nSensitivity and gaps'),('Select','Deployment anchor\nExpansion policy'),('Design','Intake and companion\nArchitect review')]
  for i,(t,d) in enumerate(labels):
   x=15+i*360;box(x,70,330,160,t,d)
   if i<4:arrow(x+330,150,x+355,150)
  dr.line((1650,250,1650,350,180,350,180,250),fill='#5b7f71',width=4)
  dr.polygon([(180,250),(171,265),(189,265)],fill='#5b7f71')
  dr.text((570,375),'Refine inputs and recompile as evidence improves',font=font(28),fill='#315a49')
 else:
  box(15,170,340,150,'Customer datacenter','Source systems\nOutside sizing scope')
  box(505,170,350,150,'Factory border','North–south path\nIngress and egress')
  box(1030,15,600,135,'GPU compute pool','Dedicated east–west fabric')
  box(1030,330,600,135,'Storage services','Physically dedicated storage fabric')
  arrow(355,240,505,240);dr.text((350,110),'External link',font=font(25,True),fill='#172e3c')
  dr.line((855,240,935,240,935,80,1030,80),fill='#34556b',width=4)
  arrow(950,80,1030,80)
  dr.line((935,240,935,395,1030,395),fill='#34556b',width=4);arrow(950,395,1030,395)
  arrow(1410,150,1410,330)
  dr.text((1440,220),'Storage I/O',font=font(25),fill='#172e3c')
 p=OUT/(name+'.png');im.save(p);return p

d=Document();s=d.sections[0];s.page_width=Inches(8.27);s.page_height=Inches(11.69)
s.top_margin=Inches(.65);s.bottom_margin=Inches(.65);s.left_margin=s.right_margin=Inches(.7)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
 st=d.styles[name];st.font.name='Arial';st.font.color.rgb=RGBColor.from_string('18242B')
 for node in list(st.element.iter(qn('w:pBdr'))):node.getparent().remove(node)
d.styles['Normal'].font.size=Pt(10.5);d.styles['Normal'].paragraph_format.space_after=Pt(7)
d.styles['Normal'].paragraph_format.line_spacing=1.08
d.styles['Title'].font.size=Pt(24);d.styles['Title'].font.color.rgb=RGBColor(0,0,0)
d.styles['Heading 1'].font.size=Pt(17);d.styles['Heading 1'].paragraph_format.space_after=Pt(10)
d.styles['Heading 2'].font.size=Pt(12);d.styles['Heading 2'].paragraph_format.space_before=Pt(10)
s.header.paragraphs[0].text='ANUBIS  /  WORKLOAD SIZING METHODOLOGY'
s.header.paragraphs[0].runs[0].font.size=Pt(8)
p=s.footer.paragraphs[0];p.text='Version 2.0 • Draft for review • 1 November 2026';p.runs[0].font.size=Pt(8)
p.add_run(' '*10);f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');p._p.append(f)
def para(text,style=None):
 p=d.add_paragraph(style=style)
 for x in re.split(r'(https?://\S+)',text):
  if x.startswith('http'):
   h=OxmlElement('w:hyperlink');h.set(qn('r:id'),p.part.relate_to(x,RT.HYPERLINK,is_external=True));r=OxmlElement('w:r');pr=OxmlElement('w:rPr');c=OxmlElement('w:color');c.set(qn('w:val'),'17365D');pr.append(c);r.append(pr);t=OxmlElement('w:t');t.text=x;r.append(t);h.append(r);p._p.append(h)
  else:p.add_run(x)
 return p
lines=source.read_text().splitlines();i=0
while i<len(lines):
 line=lines[i];i+=1
 if not line:continue
 if line=='@page':d.add_page_break();continue
 if line.startswith('@figure '):d.add_picture(str(figure(line.split()[1])),width=Inches(6.87));continue
 if line.startswith('@eq '):
  p=para(line[4:]);p.paragraph_format.space_after=Pt(4)
  for r in p.runs:r.font.name='Courier New';r.font.size=Pt(9)
  continue
 if line.startswith('|'):
  rows=[line]
  while i<len(lines) and lines[i].startswith('|'):rows.append(lines[i]);i+=1
  data=[[x.strip() for x in row.strip('|').split('|')] for row in rows]
  t=d.add_table(rows=0,cols=len(data[0]));t.autofit=False
  widths=[2.1,4.77] if len(data[0])==2 else [1.55,2.66,2.66]
  for col,w in zip(t.columns,widths):col.width=Inches(w)
  for j,values in enumerate(data):
   row=t.add_row();row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
   if j==0:row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
   for cell,value,w in zip(row.cells,values,widths):
    cell.width=Inches(w);p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(6);p.paragraph_format.space_before=Pt(5);p.paragraph_format.line_spacing=1.03
    r=p.add_run(value);r.font.size=Pt(9.5);r.bold=j==0
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EFF3' if j==0 else ('F5F7F8' if j%2==0 else 'FFFFFF'));cell._tc.get_or_add_tcPr().append(sh)
  d.add_paragraph().paragraph_format.space_after=Pt(0)
  continue
 if line.startswith('### '):para(line[4:],'Heading 2')
 elif line.startswith('## '):para(line[3:],'Heading 1')
 elif line.startswith('# '):para(line[2:],'Title')
 else:para(line)
d.core_properties.title='Anubis AI Factory Workload Sizing Methodology'
d.core_properties.subject='Version 2.0 draft with implementation scope and progressive qualification'
d.core_properties.author='Traiano Giuseppe Welcome'
d.save(OUT/'Anubis_Workload_Sizing_Methodology_v2_Draft.docx')
paths=['docs/anubis-framework.md','docs/anubis-framework-v2.txt','src/application/characterization/guided.hpp','src/compiler/planning.cpp','src/compiler/network_plan.hpp','knowledge/architecture-core.json','knowledge/guided-intake.json','knowledge/planning.json','deliverables/scenario-video/projection.json','docs/qualification-options.md']
(OUT/'source-manifest.json').write_text(json.dumps({'inspected_date':'2026-11-01','status':'Draft for review','files':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in paths]},indent=2))
print(OUT/'Anubis_Workload_Sizing_Methodology_v2_Draft.docx')
