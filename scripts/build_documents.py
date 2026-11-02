from pathlib import Path
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables'
QA = ROOT / '.document-build'
OUT.mkdir(exist_ok=True)
QA.mkdir(exist_ok=True)

def font(size, bold=False):
    path = '/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf'
    return ImageFont.truetype(path, size)

def diagram(name, labels, subtitle):
    im = Image.new('RGB', (1800, 410), 'white')
    d = ImageDraw.Draw(im)
    n=len(labels); gap=38; left=12; w=(1776-gap*(n-1))//n
    for i,(title,detail) in enumerate(labels):
        x=left+i*(w+gap)
        d.rounded_rectangle((x,35,x+w,275),radius=10,fill='#F4F6F8',outline='#8696A5',width=3)
        for y,text,bold,size in [(80,title,True,29),(145,detail,False,24)]:
            lines=text.split('\n')
            for k,line in enumerate(lines):
                box=d.textbbox((0,0),line,font=font(size,bold))
                d.text((x+(w-box[2])/2,y+k*34),line,fill='black',font=font(size,bold))
        if i<n-1:
            ax=x+w+5; bx=ax+gap-10
            d.line((ax,154,bx,154), fill='#354D63',width=4)
            d.polygon([(bx,154),(bx-11,146),(bx-11,162)],fill='#354D63')
    d.text((20,323),subtitle,fill='#354D63',font=font(25))
    p=QA/(name+'.png'); im.save(p); return p

fig1=diagram('framework-flow',[
    ('Customer intent','Consultant and\noptional agent'),
    ('Workload model','Reviewed inputs\nand scenarios'),
    ('Anubis sizing','Intended configuration\nand evidence'),
    ('Design projection','Existing fields\nand explicit mapping'),
    ('Architecture','Design compilation\nand domain review')
], 'Review creates a new upstream revision; intended hardware remains independent of the downstream design tool mapping.')
fig2=diagram('architecture-flow',[
    ('API clients','GUI  |  CLI\nOptional MCP'),
    ('Application','Authorization\nRevisions and jobs'),
    ('Pure compiler','Frozen inputs\nGoverned evidence'),
    ('Design adapter','Existing API\nMapping ledger'),
    ('Assessment','Returned artifacts\nExternal obligations')
], 'Persistence and evidence support the application; network access stays outside the deterministic core.')

def shade(cell, color):
    el=OxmlElement('w:shd'); el.set(qn('w:fill'),color); cell._tc.get_or_add_tcPr().append(el)

def hyperlink(p, text, url):
    h=OxmlElement('w:hyperlink')
    h.set(qn('r:id'),p.part.relate_to(url,RT.HYPERLINK,is_external=True))
    r=OxmlElement('w:r'); pr=OxmlElement('w:rPr')
    c=OxmlElement('w:color'); c.set(qn('w:val'),'254B6E'); pr.append(c)
    r.append(pr); t=OxmlElement('w:t'); t.text=text; r.append(t); h.append(r); p._p.append(h)

def runs(p,text):
    for part in re.split(r'(https?://\S+)',text):
        if part.startswith('http'):
            hyperlink(p,part,part)
        else:
            p.add_run(part)

def table(doc, lines):
    rows=[[x.strip() for x in line.strip().strip('|').split('|')] for line in lines]
    rows=[row for row in rows if not all(re.match(r'^[-: ]+$',c) for c in row)]
    t=doc.add_table(rows=1, cols=len(rows[0])); t.alignment=WD_TABLE_ALIGNMENT.CENTER
    t.autofit=False
    widths=([1.18,2.75,2.52] if len(rows[0])==3 else [6.45/len(rows[0])]*len(rows[0]))
    for col,width in zip(t.columns,widths): col.width=Inches(width)
    for idx,data in enumerate(rows):
        cells=t.rows[0].cells if idx==0 else t.add_row().cells
        trpr=t.rows[idx]._tr.get_or_add_trPr()
        ns=OxmlElement('w:cantSplit'); trpr.append(ns)
        if idx==0:
            h=OxmlElement('w:tblHeader'); trpr.append(h)
        for ci,(cell,value) in enumerate(zip(cells,data)):
            cell.width=Inches(widths[ci]); cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr=cell._tc.get_or_add_tcPr(); borders=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                b=OxmlElement('w:'+edge); b.set(qn('w:val'),'single'); b.set(qn('w:sz'),'4'); b.set(qn('w:color'),'D9D9D9'); borders.append(b)
            pr.append(borders); margins=OxmlElement('w:tcMar')
            for edge in ['top','left','bottom','right']:
                e=OxmlElement('w:'+edge); e.set(qn('w:w'),'90'); e.set(qn('w:type'),'dxa'); margins.append(e)
            pr.append(margins)
            shade(cell,'E5ECF2' if idx==0 else ('F7F8FA' if idx%2==0 else 'FFFFFF'))
            p=cell.paragraphs[0]; p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
            p.paragraph_format.line_spacing=1.03
            r=p.add_run(value); r.font.size=Pt(9);r.bold=idx==0
    if len(t.rows)>2:
        for cell in t.rows[-2].cells:
            for p in cell.paragraphs: p.paragraph_format.keep_with_next=True
    spacer=doc.add_paragraph();spacer.paragraph_format.space_after=Pt(3)
    spacer.paragraph_format.line_spacing=0.35

def build(src, output, academic):
    doc=Document(); sec=doc.sections[0]
    sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
    sec.top_margin=Inches(.78);sec.bottom_margin=Inches(.72);sec.left_margin=Inches(.91);sec.right_margin=Inches(.91)
    sec.footer_distance=Inches(.32)
    style=doc.styles['Normal'];style.font.name='Cambria' if academic else 'Calibri';style.font.size=Pt(10.5)
    style.paragraph_format.space_after=Pt(6);style.paragraph_format.line_spacing=1.12
    style.paragraph_format.widow_control=True
    for name,size in [('Title',24),('Subtitle',13),('Heading 1',15),('Heading 2',12),('Heading 3',11)]:
        s=doc.styles[name];s.font.name='Calibri';s.font.size=Pt(size);s.font.color.rgb=RGBColor(0,0,0)
        s.paragraph_format.keep_with_next=True
        s.paragraph_format.space_before=Pt(13 if name.startswith('Heading') else 0)
        s.paragraph_format.space_after=Pt(6)
    footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    r=footer.add_run('Anubis  |  ');r.font.size=Pt(8);r.font.color.rgb=RGBColor.from_string('666666')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    doc.core_properties.title='Anubis AI Factory Workload Sizing Framework' if academic else 'Anubis AI Factory Workload Sizing Engine Technical Architecture'
    doc.core_properties.subject='Version 1.0 methodology and implementation baseline'
    doc.core_properties.author=''
    lines=src.read_text().splitlines();i=0; subtitle=True; figure=False
    while i<len(lines):
        line=lines[i]
        if not line.strip(): i+=1;continue
        if line.startswith('```'):
            code=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'): code.append(lines[i]);i+=1
            for j,cl in enumerate(code):
                p=doc.add_paragraph();p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1
                p.paragraph_format.keep_with_next=j<len(code)-1
                r=p.add_run(cl);r.font.name='Courier New';r.font.size=Pt(8.2)
            doc.add_paragraph().paragraph_format.space_after=Pt(2)
        elif line.startswith('|'):
            chunk=[]
            while i<len(lines) and lines[i].startswith('|'):chunk.append(lines[i]);i+=1
            table(doc,chunk);continue
        elif line.startswith('# '):
            doc.add_paragraph(line[2:],'Title')
        elif line.startswith('## '):
            title=line[3:]
            if subtitle:
                doc.add_paragraph(title,'Subtitle');subtitle=False
            else:
                p=doc.add_paragraph(title,'Heading 1')
                if academic and title=='References': p.paragraph_format.page_break_before=True
        elif line.startswith('### '):
            # The numeric section label is preserved; titles have no decorative punctuation.
            doc.add_paragraph(line[4:],'Heading 2')
        elif line.startswith('    '):
            p=doc.add_paragraph();p.paragraph_format.space_after=Pt(3)
            p.paragraph_format.keep_with_next=(i+1<len(lines) and lines[i+1].startswith('    '))
            r=p.add_run(line[4:]);r.font.name='Courier New';r.font.size=Pt(8.5)
        else:
            p=doc.add_paragraph();runs(p,line)
            if line.startswith('Version '):
                for r in p.runs:r.font.size=Pt(9);r.font.color.rgb=RGBColor.from_string('555555')
            if line.startswith('['):
                p.paragraph_format.space_after=Pt(7)
                for r in p.runs:r.font.size=Pt(9)
            if (academic and line.startswith('This distinction does not confer')) or (not academic and line.startswith('The logical flow is')):
                p=doc.add_paragraph();p.paragraph_format.keep_with_next=True
                p.add_run().add_picture(str(fig1 if academic else fig2),width=Inches(6.42))
                c=doc.add_paragraph('Figure 1  '+('From customer intent to a reviewed architecture' if academic else 'Application boundaries and integration flow'))
                c.paragraph_format.space_after=Pt(9)
                for r in c.runs:r.font.size=Pt(9);r.italic=True
        i+=1
    for el in doc.styles.element.xpath('.//w:pBdr'):
        el.getparent().remove(el)
    for el in doc.element.xpath('.//w:pBdr'):
        el.getparent().remove(el)
    doc.save(output)

build(ROOT/'docs/anubis-framework.md',OUT/'Anubis_Workload_Sizing_Framework.docx',True)
build(ROOT/'docs/anubis-technical-architecture.md',OUT/'Anubis_Technical_Solution_Architecture.docx',False)
print('Built two documents in',OUT)
