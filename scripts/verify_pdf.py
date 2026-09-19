"""PDF mechanics check; visual review is recorded separately by the reviewer."""
from pathlib import Path
import json
import fitz
p=fitz.open('manuscript/main.pdf');fonts={}
for page in p:
    for f in page.get_fonts(full=True):
        if f[0] not in fonts:
            name,ext,kind,content=p.extract_font(f[0]);fonts[f[0]]=dict(name=name,type=kind,embedded=bool(content))
log=Path('results/latex_pass_2.log').read_text()
checks=dict(pages=len(p),letter_page_size=all(list(page.rect)==[0.,0.,612.,792.] for page in p),all_fonts_embedded=all(f['embedded'] for f in fonts.values()),
    no_type3_fonts=all(f['type']!='Type3' for f in fonts.values()),pdf_author_empty=not p.metadata.get('author'),undefined_references='undefined' in log.lower(),overfull_boxes='Overfull' in log)
checks['within_regular_base_limit']=checks['pages']<=7
checks['within_wip_base_limit']=checks['pages']<=6
checks['category_selected_by_author']=False
assert checks['within_regular_base_limit']
assert all(checks[k] for k in ['letter_page_size','all_fonts_embedded','no_type3_fonts','pdf_author_empty'])
assert not checks['undefined_references'] and not checks['overfull_boxes']
Path('results/pdf_verification.json').write_text(json.dumps(dict(**checks,fonts=list(fonts.values())),indent=2))
print(checks)
