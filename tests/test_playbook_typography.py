"""Run with bundled Python. Checks semantics, text preservation and real output."""
import sys,unittest
from pathlib import Path
from docx import Document
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'deliverables/usability'))
from playbook_typography import install_styles,render_inline,markup_legacy,format_playbook,STYLES

class TypographyTests(unittest.TestCase):
 def test_exact_labels_values_and_explanation(self):
  d=Document();install_styles(d);p=d.add_paragraph()
  text='Retain Factory users = One organisation. Leave Reserve dedicated capacity 1 unchecked. Click Continue. The 4 TB is the document corpus.'
  render_inline(p,markup_legacy(text))
  runs={r.text:r.style.name for r in p.runs}
  self.assertEqual(runs['Factory users'],'Anubis UI Field')
  self.assertEqual(runs['One organisation'],'Anubis UI Value')
  self.assertEqual(runs['unchecked'],'Anubis UI State')
  self.assertEqual(runs['[Continue]'],'Anubis UI Control')
  self.assertEqual(p.text,text.replace('Continue','[Continue]'))
 def test_explicit_markup_is_preserved_and_decimal_value(self):
  d=Document();install_styles(d);p=d.add_paragraph()
  render_inline(p,markup_legacy('Set [[field:Usable link fraction]] = [[value:0.7]].'))
  self.assertEqual(p.text,'Set Usable link fraction = 0.7.')
  self.assertEqual(next(r.style.name for r in p.runs if r.text=='0.7'),'Anubis UI Value')
 def test_definition_column_preserves_field_value_roles(self):
  d=Document();d.add_paragraph('The customer application')
  t=d.add_table(rows=2,cols=5)
  for c,v in zip(t.rows[0].cells,['ID','Workflow field','Definition and scope','Value or action','Basis']):c.text=v
  for c,v in zip(t.rows[1].cells,['I01','Compute location 1','Location of the activity','In this factory','Default']):c.text=v
  format_playbook(d)
  self.assertEqual(t.cell(1,1).paragraphs[0].runs[0].style.name,'Anubis UI Field')
  self.assertEqual(t.cell(1,3).paragraphs[0].runs[0].style.name,'Anubis UI Value')
  self.assertNotEqual(t.cell(1,2).paragraphs[0].runs[0].style.name,'Anubis UI Value')
 def test_current_manual(self):
  d=Document(ROOT/'deliverables/scenario-video/Anubis_Bracken_Engineering_Playbook.docx')
  cells=[c for t in d.tables for row in t.rows for c in row.cells]
  text='\n'.join(p.text for p in d.paragraphs)+''.join(c.text for c in cells)
  self.assertNotIn('[[',text)
  for _,(name,font,color,bold,italic) in STYLES.items():
   s=d.styles[name];self.assertEqual(s.font.name,font);self.assertEqual(str(s.font.color.rgb),color)
  steps=[t for t in d.tables if [c.text for c in t.rows[0].cells]==['Step','Activity and values','Screen reference']]
  self.assertEqual(len(steps),12)
  for t in steps:
   self.assertGreater(len(t.rows[1].cells[1].paragraphs),1)
  p=next(c for c in cells if 'Retain Factory users' in c.text)
  styled={r.text:r.style.name for para in p.paragraphs for r in para.runs}
  self.assertEqual(styled['Existing service outside this AI Factory'],'Anubis UI Value')

if __name__=='__main__':unittest.main()
