from pathlib import Path
import re,subprocess
root=Path(__file__).resolve().parents[1]
source=(root/'manuscript'/'main.tex').read_text()
review=re.sub(r'pdfauthor=\{[^}]*\}', 'pdfauthor={}', source)
review=re.sub(r'\\author\{.*?(?=\\begin\{document\})',lambda _: '\\author{\\IEEEauthorblockN{Author 1 \\and Author 2}}\n',review,flags=re.S)
review=review.replace(r'\section*{Acknowledgment}',r'\section*{AI Assistance Disclosure}')
(root/'manuscript'/'review.tex').write_text(review)
for name in ['main','review']:
    for i in range(2):
        label='latex' if name=='main' else 'latex_review'
        with (root/'results'/f'{label}_pass_{i+1}.log').open('w') as log:
            subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',f'{name}.tex'],cwd=root/'manuscript',stdout=log,stderr=subprocess.STDOUT,check=True)
    print(f'Built manuscript/{name}.pdf')
