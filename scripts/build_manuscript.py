from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
for i in range(2):
    with (root/'results'/f'latex_pass_{i+1}.log').open('w') as log:
        subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=root/'manuscript',stdout=log,stderr=subprocess.STDOUT,check=True)
print('Built manuscript/main.pdf')
