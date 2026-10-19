#!/usr/bin/env python3
"""Builds self-contained PREVIEW-*.html files (CSS, JS and product data inlined,
images from the Printful CDN) so a page renders fully inside a chat preview."""
import json, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'previews'; OUT.mkdir(exist_ok=True)
css = (ROOT/'assets/site.css').read_text()
js = (ROOT/'assets/site.js').read_text()
products = (ROOT/'data/products.json').read_text()
import base64
def _bake(path):
    """captured tiles are jpgs on the tile colour; knock that colour out from the edges so they behave like printful's transparent pngs."""
    try:
        from PIL import Image, ImageDraw
        import io
        im = Image.open(path).convert('RGBA')
        w, h = im.size
        px = im.load()
        bg = px[2, 2][:3]
        seen = bytearray(w * h)
        stack = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
        tol = 14
        while stack:
            x, y = stack.pop()
            if x < 0 or y < 0 or x >= w or y >= h or seen[y * w + x]:
                continue
            r, g, b, a = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > tol:
                continue
            seen[y * w + x] = 1
            px[x, y] = (r, g, b, 0)
            stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        if sum(seen) < w * h * 0.2:  # photo (blanket): keep as-is
            return 'data:image/jpeg;base64,' + base64.b64encode(path.read_bytes()).decode()
        buf = io.BytesIO(); im.save(buf, 'PNG', optimize=True)
        return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return 'data:image/jpeg;base64,' + base64.b64encode(path.read_bytes()).decode()

imgs = {p.stem: _bake(p) for p in (ROOT/'previews/img').glob('*.jpg')} if (ROOT/'previews/img').exists() else {}
def needed(src, seed):
    data = json.loads(products); ids = set()
    if 'index' in src:
        ids.add('1076503569082fa8eff33')
        for p in data:
            for c in p['colors']: ids.update(c['images'][:2])
    elif 'shop' in src or '404' in src:
        for p in data: ids.update(p['colors'][0]['images'][:2])
    elif 'product' in src:
        pid = seed.split("'")[1]
        for p in data:
            if p['id'] == pid:
                for c in p['colors']: ids.update(c['images'][:2])
            else: ids.update(p['colors'][0]['images'][:2])
    elif 'bag' in src:
        ids.update(['1076503569082fa8c6b7b','1076512869083ad57f2d1'])
    return {i: imgs[i] for i in ids if i in imgs}
fav = (ROOT/'assets/favicon.svg').read_text().replace('"', "'").replace('#','%23').replace('\n','')
pages = {
  'index.html': ('PREVIEW-home.html', ''),
  'shop.html': ('PREVIEW-shop.html', ''),
  'product.html': ('PREVIEW-product-hoodie.html', "window.PREVIEW_PRODUCT='hoodie';"),
  'product.html#2': ('PREVIEW-product-beanie.html', "window.PREVIEW_PRODUCT='beanie';"),
  'bag.html': ('PREVIEW-bag.html', "window.PREVIEW_BAG=[{variant:10765036,product:'hoodie',name:'the 345 hoodie',color:'Black',size:'M',price:40,qty:1,image:'1076503569082fa8c6b7b',printful:'https://345loveyours.printful.me/product/hoodie-345-message',listing:'the 345 hoodie',cover:false},{variant:10765128,product:'hat-denim',name:'the 345 hat | denim',color:'Black',size:'One size',price:25,qty:2,image:'1076512869083ad57f2d1',printful:'https://345loveyours.printful.me/product/denim-hat-white-logo',listing:'the 345 hat | denim',cover:false}];"),
  '404.html': ('PREVIEW-404.html', ''),
  'thanks.html': ('PREVIEW-thanks.html', ''),
  'story.html': ('PREVIEW-story.html', ''),
}
for src, (dst, seed) in pages.items():
    html = (ROOT/src.split('#')[0]).read_text()
    html = re.sub(r'<link rel="stylesheet" href="assets/site.css">', '<style>\n'+css+'\n</style>', html)
    html = html.replace('<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">', f'<link rel="icon" href="data:image/svg+xml,{fav}">')
    html = html.replace('<base href="/">', '')
    html = html.replace('<script src="assets/site.js"></script>', '<script>window.PRODUCTS='+products+';window.PREVIEW_IMG='+json.dumps(needed(src, seed))+';'+seed+'</script>\n<script>\n'+js+'\n</script>')
    # relative links point at the live site so nav works from the preview
    html = re.sub(r'href="(index|shop|product|bag)\.html', r'href="https://ily345.com/\1.html', html)
    html = html.replace("href=\"shop.html", "href=\"https://ily345.com/shop.html")
    (OUT/dst).write_text(html)
    print(dst, len(html)//1024, 'KB')
