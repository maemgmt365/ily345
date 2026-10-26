#!/usr/bin/env python3
"""Builds data/products.json (what the site renders) from data/printful-raw.json
(what Printful exposes) plus the editorial copy below.

To add or rearrange a product: edit PRODUCTS below (order = order on the site),
then run:  python3 tools/build-products.py
To refresh sizes, prices, colours or mockups from Printful, re-pull
data/printful-raw.json (see tools/README.md) and run this again.
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
raw = {p["slug"]: p for p in json.loads((ROOT / "data/printful-raw.json").read_text())}
# Printful catalog variants (from GET /products/{id}) and the product template that carries each
# listing's design. Orders are placed with variant_id + product_template_id, because the quick
# store's own sync variants are not reachable through the API.
catalog = json.loads((ROOT / "data/printful-catalog.json").read_text())
TEMPLATES = {  # printful listing id -> product template id (same colour set)
    659139: 95293780, 659138: 95293770, 659109: 95254051, 659082: 95254054, 659105: 95287559,
    659103: 95280297, 659081: 95253882, 659079: 95253842, 659101: 95254482, 659099: 95254467,
    659088: 95254210, 659086: 95254203, 659084: 95254159, 659047: 95253239, 659001: 95253329,
    658998: 95253432, 658997: 95253561,
}
# which mockup is the real back view (with the message) per Printful catalog product:
# printful's mock order is front, left, right, back for tees and sweatshirts.
BACK_INDEX = {508: 2, 411: 3}
def reorder_mocks(pid, mocks):
    i = BACK_INDEX.get(pid)
    if i is None or i >= len(mocks):
        return mocks
    return [mocks[0], mocks[i]] + [m for j, m in enumerate(mocks) if j not in (0, i)]

def catalog_variant(pid, color, size):
    same = [v for v in catalog[str(pid)] if v["color"] == color]
    m = [v for v in same if v["size"] == size] if size != "One size" else (same if len(same) == 1 else [v for v in same if v["size"] in (None, "", "One size")])
    if len(m) != 1:
        sys.exit(f"catalog lookup failed for {pid} {color} {size}")
    return m[0]["id"]

MESSAGE = [
    "3 | 4 | 5 is more than clothing. it is a message.",
    "for the moments when words go unsaid, this is a way to say: i love you. i believe in you. i am proud of you.",
    "a quiet reminder that someone is thinking of you, or a daily nudge to speak what we often keep inside.",
    "love yours.",
]

BACK_NOTE = "this piece carries the 3 | 4 | 5 message on the back, a way to say what we don't always say out loud. the hope is that one day it is understood, and doesn't need to be written at all."
SLEEVE_NOTE = "this piece has a blank back. \"love yours.\" is embroidered on the sleeve instead, a more subtle, everyday reminder. the hope is that one day 3 | 4 | 5 speaks loud enough on its own that we won't need to print the message at all."
LOGO_NOTE = "the 3 | 4 | 5 mark, embroidered. small on purpose."

# Order here is the order on the site. Each colour points at the Printful listing it lives in.
PRODUCTS = [
    {
        "id": "hoodie",
        "name": "the 345 hoodie",
        "short": "the one that started it",
        "price": {"base": 54, "plus": 54},
        "category": "hoodies",
        "placement": "front chest mark, message on back",
        "intro": "the first 345 piece and still the one most people reach for. a classic heavyweight hoodie, cotton-faced and soft inside, with the 3 | 4 | 5 mark small on the chest and the full message across the back.",
        "note": BACK_NOTE,
        "details": ["100% cotton face", "65% ring-spun cotton, 35% polyester", "front pouch pocket", "self-fabric patch on the back", "matching flat drawstrings", "3-panel hood", "unisex fit"],
        "colors": [
            ("hoodie-345-message", "Black"),
            ("hoodie-345-message", "Vintage Black"),
            ("hoodie-345-message", "Latte"),
            ("hoodie-345-message-6908305645ab5", "White"),
            ("limited-color-hoodie-white-logo", "Maroon", "limited"),
            ("limited-color-hoodie-white-logo", "Forest Green", "limited"),
            ("limited-color-hoodie-white-logo", "Adobe", "limited"),
            ("limited-color-hoodie-white-logo", "Dusty Rose", "limited"),
            ("limited-color-hoodie-white-logo", "Team Gold", "limited"),
            ("limited-color-hoodie-white-logo", "Carolina Blue", "limited"),
        ],
    },
    {
        "id": "oversized-hoodie",
        "name": "the oversized hoodie",
        "short": "heavier, roomier, quieter",
        "price": {"base": 62, "plus": 62},
        "category": "hoodies",
        "placement": "front chest mark, love yours. on the sleeve, blank back",
        "intro": "thicker, roomier and quieter than the original. brushed fleece, dropped shoulders, no drawcords. the mark sits on the chest and love yours. runs down the sleeve, so the back stays clean.",
        "note": SLEEVE_NOTE,
        "details": ["60% Airlume combed and ring-spun cotton, 40% polyester fleece", "10 oz/yd² (339 g/m²)", "brushed interior fleece", "roomy unisex fit", "double-layered hood, no drawcord", "front pocket"],
        "colors": [
            ("oversized-hoodie", "Vintage Black"),
            ("oversized-hoodie", "Asphalt"),
            ("oversized-hoodie", "Vintage Brown"),
            ("love-yours-oversized-logo-hoodie", "White"),
        ],
    },
    {
        "id": "crewneck",
        "name": "the crewneck",
        "short": "the everyday one",
        "price": {"base": 50, "plus": 50},
        "category": "sweatshirts",
        "placement": "front chest mark, message on back",
        "intro": "a straight crewneck sweatshirt with a ribbed collar and cuffs, soft fleece inside. the mark on the chest, the message on the back. it runs small, so size up.",
        "note": BACK_NOTE,
        "details": ["100% cotton face", "65% cotton, 35% polyester", "8.5 oz/yd² (288 g/m²)", "tightly knit 3-end fleece", "side-seamed", "self-fabric patch on the back", "runs small: order one size up"],
        "colors": [
            ("crewneck-345-meaning", "Black"),
            ("crewneck-345-meaning", "Vintage Black"),
            ("crewneck-345-meaning", "Latte"),
            ("crewneck-345-meaning-690836b5d8a89", "White"),
        ],
    },
    {
        "id": "tee-mens",
        "name": "the heavyweight tee",
        "short": "structured, boxy, built to last",
        "price": {"base": 38, "plus": 38},
        "category": "tees",
        "placement": "front chest mark, message on back",
        "intro": "a heavyweight tee with a structured, slightly boxy fit that holds its shape. the mark sits small on the left chest and the message runs across the back.",
        "note": BACK_NOTE,
        "details": ["100% combed ring-spun cotton", "6.5 oz/yd² (220 g/m²)", "regular fit", "side-seamed", "1 × 1 rib collar"],
        "colors": [
            ("t-shirt-345-message", "Black"),
            ("t-shirt-black-logo-embroidered", "White"),
        ],
    },
    {
        "id": "tee-womens",
        "name": "the women's tee",
        "short": "soft, longline, easy",
        "price": {"base": 32, "plus": 32},
        "category": "tees",
        "placement": "front chest mark, message on back",
        "intro": "a lighter, longline tee in combed ring-spun cotton with a crew neck. the mark on the chest, the message on the back. sits best with high-waisted bottoms.",
        "note": BACK_NOTE,
        "details": ["100% combed and ring-spun cotton", "4.3 oz/yd² (146 g/m²)", "longline fit, crew neck", "blind stitch on sleeves and hem", "side-seamed", "tear-away label"],
        "colors": [
            ("t-shirt-345-message-69083f03d15f5", "Black"),
            ("t-shirt-345-message-69083f03d15f5", "Vintage Black"),
            ("t-shirt-345-message-69083f03d15f5", "Latte"),
            ("t-shirt-345-message-69083f32eb958", "White"),
        ],
    },
    {
        "id": "beanie",
        "name": "the fisherman beanie",
        "short": "one size, every day",
        "price": {"base": 26, "plus": 26},
        "category": "hats",
        "placement": "embroidered mark on the cuff",
        "intro": "a ribbed fisherman beanie with the 3 | 4 | 5 mark embroidered on the cuff. one size, thick enough for real cold, short enough to wear year round.",
        "note": LOGO_NOTE,
        "details": ["100% acrylic", "wide, ribbed knit", "snug, comfortable fit", "one size fits most"],
        "colors": [
            ("hipster-beanie-white-logo", "Black"),
            ("hipster-beanie-white-logo", "Walnut"),
            ("hipster-beanie-black-logo", "Athletic Heather"),
            ("hipster-beanie-black-logo", "Ecru"),
        ],
    },
    {
        "id": "hat-distressed",
        "name": "the distressed cap",
        "short": "worn in from day one",
        "price": {"base": 28, "plus": 28},
        "category": "hats",
        "placement": "embroidered mark on the front, love yours. on the back",
        "intro": "a low-profile dad cap with a distressed brim and crown, so it looks lived in from the first wear. the mark embroidered on the front, love yours. on the back.",
        "note": LOGO_NOTE,
        "details": ["100% pre-shrunk cotton twill", "6-panel unstructured cap, low profile", "soft crown", "6 stitched rows on the brim", "adjustable hook and loop closure"],
        "colors": [
            ("love-yours-distressed-hat-69081cf23bb9d", "Black"),
            ("love-yours-distressed-hat-69081cf23bb9d", "Charcoal Grey"),
            ("love-yours-distressed-hat", "Khaki"),
        ],
    },
    {
        "id": "hat-denim",
        "name": "the denim cap",
        "short": "the clean one",
        "price": {"base": 28, "plus": 28},
        "category": "hats",
        "placement": "embroidered mark on the front, love yours. on the back",
        "intro": "a pigment-dyed denim cap, six panels, unstructured, adjustable strap. the mark on the front, love yours. on the back. the cleanest of the three hats.",
        "note": LOGO_NOTE,
        "details": ["100% cotton", "6-panel unstructured cap, low profile", "soft crown", "4 rows of visible stitching on the visor", "adjustable strap", "head circumference 21.65″ to 25.19″"],
        "colors": [
            ("denim-hat-white-logo", "Black"),
            ("denim-hat-white-logo", "Blue"),
            ("denim-hat-white-logo", "Light Blue"),
        ],
    },
    {
        "id": "blanket",
        "opaque": "#1a1a1a",
        "fill": True,
        "name": "the sherpa blanket",
        "short": "for the couch, the car, the gift",
        "price": {"base": 65, "plus": 65},
        "category": "home",
        "placement": "message embroidered on the corner",
        "intro": "fleece on one side, sherpa on the other, 50 by 60 inches. the full message is embroidered on the corner. the piece most often bought as a gift.",
        "note": "the full message is embroidered on the corner: i love you. i believe in you. i am proud of you.",
        "details": ["100% polyester fleece on one side", "100% polyester sherpa on the other", "50″ × 60″ (127 × 152 cm)"],
        "colors": [
            ("premium-sherpa-blanket-345-meaning", "Black"),
            ("premium-sherpa-blanket-345-meaning", "Fireside Brown"),
            ("premium-sherpa-blanket-345-meaning", "Heather Grey"),
        ],
    },
]

GOOD_TO_KNOW = {
    "hoodie": ["unisex fit, true to size", "machine wash cold, hang dry to protect the embroidery"],
    "oversized-hoodie": ["oversized by design: size down for a regular fit", "machine wash cold, hang dry"],
    "crewneck": ["runs small: order one size up", "machine wash cold, hang dry"],
    "tee-mens": ["regular to boxy fit, true to size", "machine wash cold, tumble low"],
    "tee-womens": ["longline fit, sizes S to L only", "machine wash cold, tumble low"],
    "beanie": ["one size fits most", "hand wash, lay flat to dry"],
    "hat-distressed": ["one size, adjustable hook and loop closure", "distressing varies piece to piece, that is the point", "spot clean"],
    "hat-denim": ["one size, adjustable strap", "pigment dye softens and fades with wear", "spot clean"],
    "blanket": ["50 x 60 inches", "machine wash cold, tumble low", "ships in its own box"],
}
SHARED_KNOW = ["made to order, one at a time, by our print partner printful", "ships from the us, usually 5 to 9 business days door to door", "wrong size or a flaw in the print: write to support345@gmail.com within 30 days and we will make it right"]

# printful's hat mockups sit smaller in their frame than the garments; scale them so every
# tile reads the same size (measured: garments fill ~95% of the mockup, hats ~79%).
ZOOM = {"beanie": 1.19, "hat-distressed": 1.19, "hat-denim": 1.19}
# mockups that are not transparent: blend their near-white background into the tile
BLEND = {"hat-denim"}

STORE = "https://345loveyours.printful.me"
# What each piece costs us at Printful (base sizes / plus sizes), from the Oct 2026 pricing audit.
# Used for the ledger (what goes to the partner) and for the at-cost promo code.
COST = {
    "hoodie": (36.83, 40.83), "oversized-hoodie": (42.22, 46.22), "crewneck": (33.23, 37.23),
    "tee-mens": (24.17, 28.17), "tee-womens": (21.73, 21.73), "beanie": (16.51, 16.51),
    "hat-distressed": (19.00, 19.00), "hat-denim": (19.86, 19.86), "blanket": (46.82, 46.82),
}
GIVE = {"ops": 0.05, "tax": 0.08, "stripe_pct": 0.029, "stripe_fixed": 0.30, "ship": 5.99}
def give_breakdown(price, cost):
    stripe = round(GIVE["stripe_pct"] * (price + GIVE["ship"]) + GIVE["stripe_fixed"], 2)
    tax = round(GIVE["tax"] * cost, 2)
    ops = round(GIVE["ops"] * price, 2)
    gives = round(price - cost - stripe - tax - ops, 2)
    return {"price": price, "cost": cost, "stripe": stripe, "tax": tax, "ops": ops, "gives": gives}

out = []
for p in PRODUCTS:
    colors = []
    base_pf = min(pr for e in p["colors"] for pr in [sz[2] for sz in raw[e[0]]["colors"][[c["color"] for c in raw[e[0]]["colors"]].index(e[1])]["sizes"]])
    for entry in p["colors"]:
        slug, cname = entry[0], entry[1]
        tag = entry[2] if len(entry) > 2 else None
        src = raw.get(slug)
        if not src:
            sys.exit(f"unknown printful slug {slug}")
        c = next((c for c in src["colors"] if c["color"] == cname), None)
        if not c:
            sys.exit(f"colour {cname} not in {slug}")
        colors.append({
            "name": c["color"],
            "hex": c["hex"],
            "tag": tag,
            "printful": f"{STORE}/product/{slug}",
            "listing": src["name"],
            "images": reorder_mocks(src["pid"], c["mocks"]),
            "template": TEMPLATES[src["id"]],
            "sizes": [{"size": s or "One size", "variant": vid, "catalogVariant": catalog_variant(src["pid"], c["color"], s or "One size"), "price": (p["price"]["plus"] if (s or "") in ("2XL","3XL","4XL") else p["price"]["base"]), "cost": (COST[p["id"]][1] if (s or "") in ("2XL","3XL","4XL") else COST[p["id"]][0]), "printfulRetail": price} for s, vid, price in c["sizes"]],
        })
    prices = sorted({s["price"] for c in colors for s in c["sizes"]})
    out.append({
        "id": p["id"], "name": p["name"], "category": p["category"], "placement": p["placement"],
        "price": prices[0], "priceMax": prices[-1], "opaque": p.get("opaque"), "fill": bool(p.get("fill")),
        "zoom": ZOOM.get(p["id"], 1), "blend": p["id"] in BLEND,
        "short": p["short"], "intro": p["intro"], "message": MESSAGE, "note": p["note"], "details": p["details"],
        "know": GOOD_TO_KNOW[p["id"]] + SHARED_KNOW,
        "give": give_breakdown(p["price"]["base"], COST[p["id"]][0]),
        "colors": colors,
    })

(ROOT / "data/products.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
n_colors = sum(len(p["colors"]) for p in out)
n_var = sum(len(c["sizes"]) for p in out for c in p["colors"])
print(f"wrote {len(out)} products, {n_colors} colourways, {n_var} variants")
