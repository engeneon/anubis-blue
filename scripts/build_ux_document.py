"""Build the UX architecture using the established Anubis document style."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Load shared formatting definitions without rebuilding the earlier deliverables.
source=(ROOT/'scripts/build_documents.py').read_text().split("\nbuild(ROOT/'docs/anubis-framework.md'")[0]
source=source.replace("sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)","sec.page_width=Inches(8.5);sec.page_height=Inches(11)")
source=source.replace("style.font.size=Pt(10.5)","style.font.size=Pt(11)")
source=source.replace("elif line.startswith('# '):", """elif line.startswith('[[FIGURE:'):
            key=line[len('[[FIGURE:'):-2]
            p=doc.add_paragraph();p.paragraph_format.keep_with_next=True
            p.add_run().add_picture(str(QA/('ux-'+key+'.png')),width=Inches(6.42))
        elif line.startswith('# '):""")
source=source.replace("doc.core_properties.subject='Version 1.0 methodology and implementation baseline'", "doc.core_properties.title='Anubis User Experience and Data Architecture'\n    doc.core_properties.subject='User experience data architecture and GUI specification version 1.0'")
exec(compile(source,str(ROOT/'scripts/build_documents.py'),'exec'))

def wireframe(kind):
    im=Image.new('RGB',(1800,1020),'white');d=ImageDraw.Draw(im)
    def box(rect,label,fill='#F3F5F7',size=27):
        d.rectangle(rect,fill=fill,outline='#8797A5',width=2)
        x,y,_,_=rect
        for i,line in enumerate(label.split('\n')): d.text((x+18,y+17+i*40),line,fill='#17212A',font=font(size))
    box((5,5,1795,80),('ANUBIS     Case: Customer workload     Scenario: Peak     Draft 12     Saved' if kind=='builder' else 'ANUBIS     Case: Customer workload     Analysis     Run R17     Revision 11'),'#E5ECF2',29)
    box((5,95,285,1005),'CASE\n\nOverview\nWorkload\nScenarios\nAnalysis\nCompare\nHandoff\nReports',size=28)
    if kind=='builder':
        box((305,95,1795,170),'Purpose > Composition > Models > Demand > Service > Data > Operations > Review',size=26)
        box((305,190,650,905),'STAGES\n\n1  Retrieval\n2  LLM inference\n3  External tool\n\nAdd stage\nList / Graph',size=28)
        box((670,190,1380,905),'LLM INFERENCE  /  DEMAND\n\nTransaction rate     [100] [requests/s]\nInput origin              [Estimated]\nScope                       [Peak scenario]\n\nPrompt length          [Unknown]\nOutput length           [400] [tokens]\n\nSource                      Customer interview\n\nNotes                       Retained as context','white',28)
        box((1400,190,1795,905),'REVIEW QUEUE\n\nContext length missing\nAffects KV cache sizing\n\nDescription: Incomplete\nModelling: Supported\nEvidence: Unresolved\n\nInspect assumption',size=26)
        box((305,925,1795,1005),'Back                      Save draft                                             Continue to Service',size=28)
    else:
        box((305,95,1795,170),'Run R17     Frozen revision 11     Peak + node failure     Result: Conditional',size=28)
        box((305,190,1380,345),'RECOMMENDED CONFIGURATION\nGPU and node counts  |  Supported demand  |  Operating envelope','white',28)
        box((305,365,1380,440),'Compute   Memory   Storage   Networks   Tenancy   Evidence',size=27)
        box((305,460,1380,735),'COMPUTE DERIVATION\nStage demand > Execution groups > Placement > Installed count\n\nChart: demand against qualified capacity\nTable: binding constraints and remaining headroom','white',27)
        box((305,755,1380,905),'ASSUMPTIONS AND VALIDATION\nMaterial unknowns, effects and next actions\nAll displayed values reference immutable result facts','white',27)
        box((1400,190,1795,905),'FACT INSPECTOR\n\nValue and scope\nInput observations\nApplied rules\nEvidence references\nQualifications\n\nOpen source\nCreate revised draft',size=27)
        box((305,925,1795,1005),'Compare run                      Select configuration                      Prepare handoff',size=28)
    path=QA/('ux-'+kind+'.png');im.save(path)
wireframe('builder');wireframe('analysis')
build(ROOT/'docs/anubis-ux-data-gui-architecture.md',OUT/'Anubis_UX_Data_and_GUI_Architecture.docx',False)
print(OUT/'Anubis_UX_Data_and_GUI_Architecture.docx')
