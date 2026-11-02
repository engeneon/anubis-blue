from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'scripts/build_documents.py').read_text().split("\nbuild(ROOT/'docs/anubis-framework.md'")[0]
source=source.replace("sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)","sec.page_width=Inches(8.5);sec.page_height=Inches(11)")
source=source.replace("style.font.size=Pt(10.5)","style.font.size=Pt(11)")
source=source.replace("if academic and title=='References':", "if title.startswith(('1 Meridian','2 Harbor','3 Aster','4 Common')):")
source=source.replace("doc.core_properties.subject='Version 1.0 methodology and implementation baseline'", "doc.core_properties.title='Anubis Customer Workload Stories'\n    doc.core_properties.subject='Three fictional scenarios for structured workload discovery'")
exec(compile(source,str(ROOT/'scripts/build_documents.py'),'exec'))
build(ROOT/'docs/anubis-customer-workload-stories.md',OUT/'Anubis_Customer_Workload_Stories.docx',False)
print(OUT/'Anubis_Customer_Workload_Stories.docx')
