"""Embed the small catalogue in the deterministic compiler; no runtime network dependency."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
j=json.loads((root/'knowledge/planning.json').read_text())
(root/'src/compiler/planning_catalog.inc').write_text('R"CATALOG('+json.dumps(j,separators=(',',':'))+')CATALOG"')
