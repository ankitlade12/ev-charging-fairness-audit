"""PDF mechanics check; visual review is recorded separately by the reviewer."""
from pathlib import Path
import argparse,json,re
import fitz
parser=argparse.ArgumentParser()
parser.add_argument('--review',action='store_true',help='Check the anonymous CCWC review copy')
args=parser.parse_args()
name='review' if args.review else 'main'
p=fitz.open(f'manuscript/{name}.pdf');fonts={}
source=Path(f'manuscript/{name}.tex').read_text()
expected_author=re.search(r'pdfauthor=\{([^}]*)\}',source).group(1)
text='\n'.join(page.get_text() for page in p)
for page in p:
    for f in page.get_fonts(full=True):
        if f[0] not in fonts:
            name,ext,kind,content=p.extract_font(f[0]);fonts[f[0]]=dict(name=name,type=kind,embedded=bool(content))
log=Path('results/latex_review_pass_2.log' if args.review else 'results/latex_pass_2.log').read_text()
checks=dict(pages=len(p),letter_page_size=all(list(page.rect)==[0.,0.,612.,792.] for page in p),all_fonts_embedded=all(f['embedded'] for f in fonts.values()),
    no_type3_fonts=all(f['type']!='Type3' for f in fonts.values()),pdf_author_empty=not p.metadata.get('author'),pdf_author_matches_source=p.metadata.get('author','')==expected_author,author_names_present=all(name.strip() in text for name in expected_author.split(';')),undefined_references='undefined' in log.lower(),overfull_boxes='Overfull' in log)
checks['within_regular_base_limit']=checks['pages']<=7
checks['within_wip_base_limit']=checks['pages']<=6
checks['category_selected_by_author']=False
if args.review:
    author_source=Path('manuscript/main.tex').read_text()
    author_names=re.search(r'pdfauthor=\{([^}]*)\}',author_source).group(1).split(';')
    checks['anonymous_review']=checks['pdf_author_empty'] and all(name.strip() not in text for name in author_names) and '@' not in text and 'Author 1' in text and 'Author 2' in text
    assert checks['anonymous_review']
assert checks['within_regular_base_limit']
assert all(checks[k] for k in ['letter_page_size','all_fonts_embedded','no_type3_fonts','pdf_author_matches_source','author_names_present'])
assert not checks['undefined_references'] and not checks['overfull_boxes']
Path('results/pdf_review_verification.json' if args.review else 'results/pdf_verification.json').write_text(json.dumps(dict(**checks,fonts=list(fonts.values())),indent=2))
print(checks)
