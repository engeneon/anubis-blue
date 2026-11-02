#!/usr/bin/env python3
"""Identify a local development build without asserting production qualification."""
import hashlib,json,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[1]
paths=[root/'build/anubis',root/'ui/dist/app.js',root/'ui/dist/style.css',root/'ui/dist/index.html',root/'contracts/openapi.json',root/'package-lock.json']
paths+=sorted((root/'src').rglob('*.cpp'))+sorted((root/'src').rglob('*.hpp'))
report={'version':'0.1.0','classification':'development-build','production_qualified':False,'git_base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'working_tree_changes_included':True,'artifacts':[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],'qualification_strategy':'hybrid-public-evidence-local-neon','external_evidence_policy':'Synthetic placement tests and methodology sources do not qualify GPU performance.'}
(root/'implementation/release-evidence/local-build-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(f'Identified {len(paths)} development artifacts')
