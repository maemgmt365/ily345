#!/usr/bin/env bash
# Downloads every product mockup from Printful's CDN into img/ so the site no longer
# depends on Printful keeping the listings alive. Run from the repo root on a machine
# with internet access, then set CONFIG.imgBase = 'img/' in assets/site.js.
set -e
mkdir -p img
python3 - <<'PY'
import json, urllib.request, os
ids = sorted({m for p in json.load(open('data/products.json')) for c in p['colors'] for m in c['images']})
for i, m in enumerate(ids, 1):
    dst = f'img/{m}.png'
    if os.path.exists(dst): continue
    urllib.request.urlretrieve(f'https://cdn.printful.me/t/quick-stores/variants/{m}', dst)
    print(f'{i}/{len(ids)} {dst}')
PY
