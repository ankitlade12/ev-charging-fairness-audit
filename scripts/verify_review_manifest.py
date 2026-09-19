from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'REVIEW_MANIFEST.json').read_text())
for name,expected in manifest.items():
    path=root/name
    if not path.is_file():raise SystemExit(f'Missing: {name}')
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual!=expected:raise SystemExit(f'Hash mismatch: {name}')
print(f'Verified {len(manifest)} review artifact files.')
