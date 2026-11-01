from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'release';out.mkdir(exist_ok=True)
with ZipFile(out/'personalized-learning-path.zip','w',ZIP_DEFLATED) as z:
    for p in sorted(ROOT.rglob('*')):
        rel=p.relative_to(ROOT)
        if not p.is_file() or any(part in {'.git','.openai','node_modules','__pycache__','release','.venv'} for part in rel.parts) or p.suffix in {'.pyc','.zip'}:continue
        z.write(p,'personalized-learning-path/'+str(rel))
print(out/'personalized-learning-path.zip')
