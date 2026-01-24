import os
from pathlib import Path
from difflib import SequenceMatcher

base = Path(__file__).resolve().parents[1]
frontend = base / 'frontend' / 'src'
frontend_next = base / 'frontend-next'

components_a = {}
components_b = {}

for root, dirs, files in os.walk(frontend):
    for f in files:
        if f.endswith(('.tsx', '.ts', '.jsx', '.js')):
            components_a.setdefault(f, []).append(Path(root) / f)

for root, dirs, files in os.walk(frontend_next):
    for f in files:
        if f.endswith(('.tsx', '.ts', '.jsx', '.js')):
            components_b.setdefault(f, []).append(Path(root) / f)

common = sorted(set(components_a.keys()) & set(components_b.keys()))

report_lines = []
report_lines.append('# Frontend Duplicate Components Report')
report_lines.append('')
report_lines.append('This report lists files with the same filename present in both `frontend` and `frontend-next`, with a simple content similarity score.')
report_lines.append('')
report_lines.append('| Filename | Path in frontend | Path in frontend-next | Similarity | Notes |')
report_lines.append('|---|---|---|---:|---|')

for name in common:
    paths_a = components_a[name]
    paths_b = components_b[name]
    # take first occurrence
    pa = paths_a[0]
    pb = paths_b[0]
    try:
        a_text = pa.read_text(encoding='utf-8', errors='ignore')
        b_text = pb.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        a_text = ''
        b_text = ''
    ratio = SequenceMatcher(None, a_text, b_text).ratio()
    note = ''
    if ratio > 0.9:
        note = 'Almost identical'
    elif ratio > 0.6:
        note = 'Similar (refactor candidate)'
    else:
        note = 'Different implementations'
    report_lines.append(f'| {name} | `{pa.relative_to(base)}` | `{pb.relative_to(base)}` | {ratio:.2f} | {note} |')

report_lines.append('')
report_lines.append('## Summary')
report_lines.append(f'- Total duplicates found: {len(common)}')
report_lines.append('')
report_path = base / 'docs' / 'FRONTEND_DUPLICATES.md'
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text('\n'.join(report_lines), encoding='utf-8')
print(f'Report generated: {report_path} (duplicates: {len(common)})')
