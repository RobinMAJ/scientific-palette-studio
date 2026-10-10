"""Refresh shared browser math/template assets without changing the website UI."""
from pathlib import Path
import argparse
import importlib.util
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--skill-source', type=Path, default=ROOT.parent)
SKILL = parser.parse_args().skill_source.resolve()
spec = importlib.util.spec_from_file_location('palette', SKILL / 'scripts/palette.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
original = (SKILL / 'assets/workbench.html').read_text(encoding='utf-8')
engine = re.search(r'<script>\s*(.*?)\s*</script>', original, re.S).group(1)
engine = engine.replace("JSON.parse(document.getElementById('payload').textContent)", 'window.PALETTE_PAYLOAD')
engine = engine.replace(' · Local, offline tool', ' · Browser-local processing').removesuffix('render();')
if 'input.oninput=' not in engine:
    engine = engine.replace('input.onchange=()=>edit(i,input.value);', 'input.oninput=()=>{if(/^#[0-9A-Fa-f]{6}$/.test(input.value))edit(i,input.value)};input.onchange=()=>edit(i,input.value);')
engine = engine.replace('p.main.slice(0,6).map(c=>c.hex)', 'Array.from({length:6},(_,i)=>p.main[i%p.main.length].hex)')
(ROOT / 'dist/assets/palette-engine.js').write_text(engine + '\n', encoding='utf-8')
palette = p.build_palette(p.DEMO_COLORS, 'Original demonstration', {'basis': 'original demonstration', 'note': 'Not extracted from a paper.'})
parts = {}
with zipfile.ZipFile(SKILL / 'assets/palette-template.pptx') as archive:
    for name in archive.namelist():
        data = archive.read(name)
        parts[name] = data.decode('utf-8') if name.endswith(('.xml', '.rels')) else list(data)
payload = {'palette': palette, 'themeParts': {k: v.decode() for k, v in p.theme_parts(palette).items()}, 'pptxParts': parts}
(ROOT / 'dist/assets/palette-data.js').write_text('window.PALETTE_PAYLOAD=' + json.dumps(payload, ensure_ascii=True, separators=(',', ':')) + ';\n', encoding='utf-8')
css = re.search(r'<style>(.*?)</style>', original, re.S).group(1)
(ROOT / 'dist/assets/engine.css').write_text(css, encoding='utf-8')
print('Refreshed palette math, native template payload and base CSS; preserved website UI/PDF ingestion.')
