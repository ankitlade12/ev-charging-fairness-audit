"""Local ICCA PDF mechanics checks; does not replace IEEE PDF eXpress."""
from pathlib import Path
import hashlib,json,re
import fitz
source=Path('manuscript/icca.tex').read_text();path=Path('manuscript/icca.pdf');doc=fitz.open(path)
text='\n'.join(page.get_text(sort=True) for page in doc)
log=Path('results/real_data/latex_pass_2.log').read_text();fonts={}
for page in doc:
    for f in page.get_fonts(full=True):
        if f[0] not in fonts:
            name,ext,kind,content=doc.extract_font(f[0]);fonts[f[0]]=dict(name=name,type=kind,embedded=bool(content))
author=re.search(r'pdfauthor=\{([^}]+)\}',source).group(1)
cited={k for group in re.findall(r'\\cite\{([^}]+)\}',source) for k in group.split(',')}
refs=re.findall(r'\\bibitem\{([^}]+)\}',source)
checks=dict(pages=len(doc),a4=all(abs(p.rect.width-595.276)<.02 and abs(p.rect.height-841.89)<.02 for p in doc),
within_six_pages=len(doc)<=6,all_fonts_embedded=all(f['embedded'] for f in fonts.values()),no_type3_fonts=all(f['type']!='Type3' for f in fonts.values()),
author_metadata=doc.metadata.get('author')==author,names_present=all(n.strip() in text for n in author.split(';')),
no_undefined_references=not re.search(r'(undefined|Rerun to get cross-references)',log,re.I),no_overfull_boxes='Overfull' not in log,
all_references_cited=cited==set(refs) and len(refs)==len(set(refs)),no_placeholders=not any(x in text for x in ['CCWC','TODO','XXXXXXXX','Author 1','Author 2']),
no_attachments=doc.embfile_count()==0,no_comments=all(not list(p.annots() or []) for p in doc),
no_page_number_footer=all(not re.search(r'^\s*\d+\s*$',p.get_text(clip=fitz.Rect(0,810,p.rect.width,p.rect.height)).strip()) for p in doc))
assert all(v for k,v in checks.items() if k!='pages'),checks
out=Path('results/real_data');out.mkdir(exist_ok=True)
(out/'pdf_verification.json').write_text(json.dumps(dict(checks=checks,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),fonts=list(fonts.values()),reference_count=len(refs),official_pdf_express=False),indent=2))
Path('final/real_data_audit').mkdir(exist_ok=True)
Path('final/real_data_audit/manuscript_text.txt').write_text(text)
for i,p in enumerate(doc):p.get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save(f'final/real_data_audit/page_{i+1}.png')
print(json.dumps(checks,indent=2))
