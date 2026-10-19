# how the site is put together

- `data/printful-raw.json`: what Printful exposes (listings, colours, sizes, variant ids, prices, mockup ids). Pulled from the storefront.
- `tools/build-products.py`: the editorial layer. Product order, names, copy, which Printful listing each colour lives in. Run it to regenerate `data/products.json`.
- `data/products.json`: what the site renders. Do not hand-edit; edit the script.
- `assets/site.css`: the whole design system. `assets/site.js`: header, footer, grid, product page, bag.
- `index.html`, `shop.html`, `product.html` (one template, `?p=<id>`), `bag.html`, `404.html`.
- `v1-previous/`: the site as it was before September 2026, untouched.

## add, remove or reorder a product
Edit `PRODUCTS` in `tools/build-products.py` (order there = order on the site), run `python3 tools/build-products.py`, deploy.

## refresh prices, sizes or colours from Printful
Open the storefront in a browser and re-pull `data/printful-raw.json` (see the notes in the Sep 2026 Claude thread), then run the build script.

## self-host the images
`./tools/fetch-images.sh` then set `imgBase: 'img/'` in `assets/site.js`.
