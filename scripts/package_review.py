"""Create a local review archive. Does not publish, upload or submit anything."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json
root=Path(__file__).resolve().parents[1]
files=[]
for name in ['README.md','pyproject.toml','requirements.lock','requirements-review.lock','.gitignore']:
    files.append(root/name)
for directory in ['src','scripts','tests','config','docs','figures','manuscript','notebooks','results']:
    for p in (root/directory).rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts:continue
        if p.suffix in ['.pyc','.aux','.log','.out','.fls','.fdb_latexmk']:continue
        if p.name in ['.DS_Store','data_exclusions.json','artifact_manifest.json']:continue
        if 'pdf_review' in p.parts and p.name!='review.json':continue
        files.append(p)
# Clear local path leaks in diagnostic transcripts; report rather than silently redact.
for p in files:
    if p.suffix in ['.txt','.md','.tex','.py','.json']:
        if str(Path.home()) in p.read_text(errors='ignore'):raise ValueError(f'Local path in archive text: {p.relative_to(root)}')
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
intro='''# Local CCWC review archive

This archive contains the review manuscript, source, synthetic experiments, aggregate data audit, notebook, figures, checks and reproducibility instructions. It has not been submitted or published externally.

Raw real-user records and private exclusion rows are omitted. The synthetic experiments run without those files.

Read README.md, docs/results_report.md and docs/submission_checklist.md before using any claim. Independent human review and final submission authorization are outstanding. No public license for newly authored code has been chosen; source is provided for this local review. The included IEEEtran class retains its own license notices.

REVIEW_MANIFEST.json hashes every supplied workspace file. To check archive integrity after extraction, run `python3 scripts/verify_review_manifest.py`. This verifies bytes, not scientific validity.
'''
archive=root/'evfair_ccwc_review.zip'
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(set(files)):z.write(p,p.relative_to(root))
    z.writestr('REVIEW_MANIFEST.json',json.dumps(manifest,indent=2))
    z.writestr('ARCHIVE_README.md',intro)
with ZipFile(archive) as z:
    assert z.testzip() is None
    for name,h in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==h
print(f'{archive.name}: {len(files)} files, {archive.stat().st_size/1e6:.2f} MB, all archived hashes verified')
