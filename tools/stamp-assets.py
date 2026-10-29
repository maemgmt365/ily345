#!/usr/bin/env python3
"""Stamp assets/site.css and assets/site.js links with a content hash so browsers and
GitHub Pages' cache pick up every deploy. Run before packaging."""
import hashlib, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
h = hashlib.sha1((ROOT / 'assets/site.css').read_bytes() + (ROOT / 'assets/site.js').read_bytes() + (ROOT / 'data/products.json').read_bytes()).hexdigest()[:8]
for f in list(ROOT.glob('*.html')) + list(ROOT.glob('p/*.html')):
    s = f.read_text()
    s2 = re.sub(r'assets/site\.(css|js)(\?v=[0-9a-f]+)?', lambda m: f'assets/site.{m.group(1)}?v={h}', s)
    if s2 != s: f.write_text(s2)
js = ROOT / 'assets/site.js'
s = js.read_text()
s2 = re.sub(r"'data/products\.json(\?v=[0-9a-f]+)?'", f"'data/products.json?v={h}'", s)
if s2 != s: js.write_text(s2)
print('stamped', h)
