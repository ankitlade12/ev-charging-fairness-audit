"""Build the active named ICCA A4 manuscript; historical drafts stay archived."""
from pathlib import Path
import shutil, subprocess
root=Path(__file__).resolve().parents[1]
latex=shutil.which('pdflatex')
if not latex:
    candidate=Path.home()/'Library/TinyTeX/bin/universal-darwin/pdflatex'
    if candidate.exists():latex=str(candidate)
if not latex:raise SystemExit('Install a LaTeX distribution providing pdflatex.')
source=root/'manuscript'/'icca.tex'
(root/'manuscript'/'main.tex').write_text(source.read_text())
out=root/'results'/'real_data';out.mkdir(parents=True,exist_ok=True)
for i in range(2):
    with (out/f'latex_pass_{i+1}.log').open('w') as log:
        subprocess.run([latex,'-interaction=nonstopmode','-halt-on-error','icca.tex'],cwd=source.parent,stdout=log,stderr=subprocess.STDOUT,check=True)
shutil.copy2(source.with_suffix('.pdf'),source.parent/'main.pdf')
(root/'final').mkdir(exist_ok=True)
shutil.copy2(source.with_suffix('.pdf'),root/'final'/'ICCA_2026_Paper.pdf')
print('Built named ICCA manuscript and final/ICCA_2026_Paper.pdf')
