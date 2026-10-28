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
    # 28 oct 2026: the dot and roman styles, the black and white 345 hoodie at mark size 2.00 with
    # charcoal heather, and dust on the oversized hoodie. Republished the same day with PNG mockups
    # (the first pass came out as JPG on a white background, which showed as a white box on the tile).
    1207559: 95253842, 1207561: 95253882, 1207565: 109467030, 1207569: 109467665, 1207576: 109467836,
    1207578: 109467363, 1207580: 109467749, 1207584: 109467853, 1207586: 109488438, 1207598: 109488451,
    1207601: 109488442, 1207607: 109488463, 1207611: 95253329, 1207616: 109468016, 1207619: 109468030,
    1207621: 109468018, 1207626: 109468040, 1207630: 109468331, 1207631: 109468347, 1207633: 109468336,
    1207636: 109468357, 1207639: 109468379, 1207643: 109468368, 1207647: 109468389, 1207657: 109468372,
    1207662: 109487533, 1207669: 109487538, 1207673: 109487548, 1207678: 109487554, 1207683: 109487560,
    1207687: 109487564, 1207690: 109487578, 1207698: 109487581, 1207703: 109487592, 1207711: 109487595,
    # corduroy cap (Big Accessories BA703): classic, dot, roman
    1208427: 109491295, 1208434: 109491351, 1208444: 109491369,
    # sweats, mark on the left thigh: Cotton Heritage M7580 (white thread on dark, black on white)
    1207790: 109495174, 1207793: 109495179, 1207801: 109495184, 1207781: 109495153, 1207785: 109495166, 1207787: 109495169,
    # oversized sweats, Bella + Canvas 4737 (white thread on black and asphalt, black on dust)
    1207813: 109495539, 1207818: 109495543, 1207824: 109495545, 1207804: 109495522, 1207807: 109495531, 1207827: 109495533,
}
# which mockup is the real back view (with the message) per Printful catalog product:
# the first listings (oct 2026) came out front, left, right, back for tees and sweatshirts.
# Listings published from 28 oct put the back second already, so only the originals are reordered.
BACK_INDEX = {508: 2, 411: 3}
ORIGINAL_LISTINGS = {659109, 659082, 659099, 659101}
def reorder_mocks(pid, mocks, listing=None):
    i = BACK_INDEX.get(pid) if listing in ORIGINAL_LISTINGS else None
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

# Styles: the same garment and colours with a different mark. "classic" lives in each product's
# "colors"; the other styles live in its "styles" dict, one list of (printful slug, colour) per style,
# each pointing at the Printful listing that carries that mark. A style with no listings yet is
# simply left out, so the site only offers what can be ordered.
STYLES = [("classic", "3 | 4 | 5"), ("dot", "3 · 4 · 5"), ("roman", "III · IV · V")]
STYLE_LINE = {
    "classic": "the original mark: 3 | 4 | 5, with the pipes.",
    "dot": "the same three numbers, joined by dots: 3 · 4 · 5.",
    "roman": "the same three numbers, written the old way: III · IV · V.",
}
def restyle(text, label):
    return text.replace("the 3 | 4 | 5 mark", f"the {label} mark")

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
            ("the-345-hoodie-classic-png", "Black"),
            ("the-345-hoodie-classic-png", "Vintage Black"),
            ("the-345-hoodie-classic-png", "Charcoal Heather"),
            ("the-345-hoodie-classic-png", "Latte"),
            ("the-345-hoodie-white-classic-png", "White"),
            ("limited-color-hoodie-white-logo", "Maroon", "limited"),
            ("limited-color-hoodie-white-logo", "Forest Green", "limited"),
            ("limited-color-hoodie-white-logo", "Adobe", "limited"),
            ("limited-color-hoodie-white-logo", "Dusty Rose", "limited"),
            ("limited-color-hoodie-white-logo", "Team Gold", "limited"),
            ("limited-color-hoodie-white-logo", "Carolina Blue", "limited"),
        ],
        "styles": {
            "dot": [
                ("the-345-hoodie-dot-png", "Black"),
                ("the-345-hoodie-dot-png", "Vintage Black"),
                ("the-345-hoodie-dot-png", "Charcoal Heather"),
                ("the-345-hoodie-dot-png", "Latte"),
                ("the-345-hoodie-white-dot-png", "White"),
                ("the-345-hoodie-colors-dot-png", "Maroon", "limited"),
                ("the-345-hoodie-colors-dot-png", "Forest Green", "limited"),
                ("the-345-hoodie-colors-dot-png", "Adobe", "limited"),
                ("the-345-hoodie-colors-dot-png", "Dusty Rose", "limited"),
                ("the-345-hoodie-colors-dot-png", "Team Gold", "limited"),
                ("the-345-hoodie-colors-dot-png", "Carolina Blue", "limited"),
            ],
            "roman": [
                ("the-345-hoodie-roman-png", "Black"),
                ("the-345-hoodie-roman-png", "Vintage Black"),
                ("the-345-hoodie-roman-png", "Charcoal Heather"),
                ("the-345-hoodie-roman-png", "Latte"),
                ("the-345-hoodie-white-roman-png", "White"),
                ("the-345-hoodie-colors-roman-png", "Maroon", "limited"),
                ("the-345-hoodie-colors-roman-png", "Forest Green", "limited"),
                ("the-345-hoodie-colors-roman-png", "Adobe", "limited"),
                ("the-345-hoodie-colors-roman-png", "Dusty Rose", "limited"),
                ("the-345-hoodie-colors-roman-png", "Team Gold", "limited"),
                ("the-345-hoodie-colors-roman-png", "Carolina Blue", "limited"),
            ],
        },
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
            ("the-345-hoodie-oversized-dust-png", "Dust"),
        ],
        "styles": {
            "dot": [
                ("the-345-hoodie-oversized-dot-png", "Vintage Black"),
                ("the-345-hoodie-oversized-dot-png", "Asphalt"),
                ("the-345-hoodie-oversized-dot-png", "Vintage Brown"),
                ("the-345-hoodie-oversized-white-dust-dot-png", "White"),
                ("the-345-hoodie-oversized-white-dust-dot-png", "Dust"),
            ],
            "roman": [
                ("the-345-hoodie-oversized-roman-png", "Vintage Black"),
                ("the-345-hoodie-oversized-roman-png", "Asphalt"),
                ("the-345-hoodie-oversized-roman-png", "Vintage Brown"),
                ("the-345-hoodie-oversized-white-dust-roman-png", "White"),
                ("the-345-hoodie-oversized-white-dust-roman-png", "Dust"),
            ],
        },
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
        "styles": {
            "dot": [
                ("the-345-crewneck-dot-png", "Black"),
                ("the-345-crewneck-dot-png", "Vintage Black"),
                ("the-345-crewneck-dot-png", "Latte"),
                ("the-345-crewneck-white-dot-png", "White"),
            ],
            "roman": [
                ("the-345-crewneck-roman-png", "Black"),
                ("the-345-crewneck-roman-png", "Vintage Black"),
                ("the-345-crewneck-roman-png", "Latte"),
                ("the-345-crewneck-white-roman-png", "White"),
            ],
        },
    },
    {
        "id": "sweats",
        "name": "the 345 sweats",
        "short": "the everyday pair",
        "price": {"base": 44, "plus": 44},
        "category": "sweats",
        "placement": "embroidered mark on the left thigh",
        "intro": "fleece sweatpants with cuffed ankles and a soft, brushed inside. the 3 | 4 | 5 mark sits small on the left thigh, the same mark as the chest, so they pair with any of the tops.",
        "note": LOGO_NOTE,
        "details": ["100% cotton face", "65% cotton, 35% polyester (charcoal heather is 55% cotton, 45% polyester)", "tightly knit 3-end fleece", "cuffed and side-seamed legs", "elastic waistband with flat drawstrings", "2 front pockets, 1 back patch pocket"],
        "colors": [
            ("the-345-sweats", "Black"),
            ("the-345-sweats", "Charcoal Heather"),
            ("the-345-sweats-white", "White"),
            ("the-345-sweats", "Maroon"),
            ("the-345-sweats", "Dusty Rose"),
        ],
        "styles": {
            "dot": [
                ("the-345-sweats-dot", "Black"),
                ("the-345-sweats-dot", "Charcoal Heather"),
                ("the-345-sweats-white-dot", "White"),
                ("the-345-sweats-dot", "Maroon"),
                ("the-345-sweats-dot", "Dusty Rose"),
            ],
            "roman": [
                ("the-345-sweats-roman", "Black"),
                ("the-345-sweats-roman", "Charcoal Heather"),
                ("the-345-sweats-white-roman", "White"),
                ("the-345-sweats-roman", "Maroon"),
                ("the-345-sweats-roman", "Dusty Rose"),
            ],
        },
    },
    {
        "id": "oversized-sweats",
        "name": "the oversized sweats",
        "short": "heavier, roomier, a 90s cut",
        "price": {"base": 58, "plus": 58},
        "category": "sweats",
        "placement": "embroidered mark on the left thigh",
        "intro": "heavyweight sweatpants with a relaxed, boxy fit and brushed fleece inside. deep side pockets and elastic cuffs. the mark sits small on the left thigh. made to go with the oversized hoodie.",
        "note": LOGO_NOTE,
        "details": ["60% cotton, 40% polyester fleece", "10 oz/yd² (339 g/m²)", "relaxed, boxy fit", "deep side pockets, elastic cuffs, interior drawcord", "soft brushed fleece inside"],
        "colors": [
            ("the-345-sweats-oversized", "Black"),
            ("the-345-sweats-oversized", "Asphalt"),
            ("the-345-sweats-oversized-dust", "Dust"),
        ],
        "styles": {
            "dot": [
                ("the-345-sweats-oversized-dot", "Black"),
                ("the-345-sweats-oversized-dot", "Asphalt"),
                ("the-345-sweats-oversized-dust-dot", "Dust"),
            ],
            "roman": [
                ("the-345-sweats-oversized-roman", "Black"),
                ("the-345-sweats-oversized-roman", "Asphalt"),
                ("the-345-sweats-oversized-dust-roman", "Dust"),
            ],
        },
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
        "styles": {
            "dot": [
                ("the-345-tee-mens-dot-png", "Black"),
                ("the-345-tee-mens-white-dot-png", "White"),
            ],
            "roman": [
                ("the-345-tee-mens-roman-png", "Black"),
                ("the-345-tee-mens-white-roman-png", "White"),
            ],
        },
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
        "styles": {
            "dot": [
                ("the-345-tee-womens-dot-png", "Black"),
                ("the-345-tee-womens-dot-png", "Vintage Black"),
                ("the-345-tee-womens-dot-png", "Latte"),
                ("the-345-tee-womens-white-dot-png", "White"),
            ],
            "roman": [
                ("the-345-tee-womens-roman-png", "Black"),
                ("the-345-tee-womens-roman-png", "Vintage Black"),
                ("the-345-tee-womens-roman-png", "Latte"),
                ("the-345-tee-womens-white-roman-png", "White"),
            ],
        },
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
        "styles": {
            "dot": [
                ("the-345-beanie-white-logo-dot-png", "Black"),
                ("the-345-beanie-white-logo-dot-png", "Walnut"),
                ("the-345-beanie-black-logo-dot-png", "Athletic Heather"),
                ("the-345-beanie-black-logo-dot-png", "Ecru"),
            ],
            "roman": [
                ("the-345-beanie-white-logo-roman-png", "Black"),
                ("the-345-beanie-white-logo-roman-png", "Walnut"),
                ("the-345-beanie-black-logo-roman-png", "Athletic Heather"),
                ("the-345-beanie-black-logo-roman-png", "Ecru"),
            ],
        },
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
        "styles": {
            "dot": [
                ("the-345-hat-distressed-black-charcoal-dot-png", "Black"),
                ("the-345-hat-distressed-black-charcoal-dot-png", "Charcoal Grey"),
                ("the-345-hat-distressed-khaki-dot-png", "Khaki"),
            ],
            "roman": [
                ("the-345-hat-distressed-black-charcoal-roman-png", "Black"),
                ("the-345-hat-distressed-black-charcoal-roman-png", "Charcoal Grey"),
                ("the-345-hat-distressed-khaki-roman-png", "Khaki"),
            ],
        },
    },
    {
        "id": "hat-denim",
        "name": "the denim cap",
        "short": "the clean one",
        "price": {"base": 28, "plus": 28},
        "category": "hats",
        "placement": "embroidered mark on the front, love yours. on the back",
        "intro": "a pigment-dyed denim cap, six panels, unstructured, adjustable strap. the mark on the front, love yours. on the back. the cleanest of the caps.",
        "note": LOGO_NOTE,
        "details": ["100% cotton", "6-panel unstructured cap, low profile", "soft crown", "4 rows of visible stitching on the visor", "adjustable strap", "head circumference 21.65″ to 25.19″"],
        "colors": [
            ("denim-hat-white-logo", "Black"),
            ("denim-hat-white-logo", "Blue"),
            ("denim-hat-white-logo", "Light Blue"),
        ],
        "styles": {
            "dot": [
                ("the-345-hat-denim-dot-png", "Black"),
                ("the-345-hat-denim-dot-png", "Blue"),
                ("the-345-hat-denim-dot-png", "Light Blue"),
            ],
            "roman": [
                ("the-345-hat-denim-roman-png", "Black"),
                ("the-345-hat-denim-roman-png", "Blue"),
                ("the-345-hat-denim-roman-png", "Light Blue"),
            ],
        },
    },
    {
        "id": "hat-corduroy",
        "name": "the corduroy cap",
        "short": "soft, warm, a little vintage",
        "price": {"base": 28, "plus": 28},
        "category": "hats",
        "placement": "embroidered mark on the front, love yours. on the back",
        "intro": "a vintage corduroy cap, six panels, unstructured, with an adjustable strap and a gold-colored buckle. the mark on the front, love yours. on the back. the warmest of the caps, and it pairs with the browns and creams.",
        "note": LOGO_NOTE,
        "details": ["100% cotton corduroy", "6-panel unstructured cap, low profile", "cotton twill sweatband and taping", "6 embroidered eyelets", "adjustable strap with a gold-colored metal buckle", "head circumference 20″ to 22″"],
        "colors": [
            ("the-345-hat-corduroy-v2", "Black"),
            ("the-345-hat-corduroy-v2", "Brown"),
            ("the-345-hat-corduroy-v2", "Burgundy"),
            ("the-345-hat-corduroy-v2", "Olive"),
        ],
        "styles": {
            "dot": [
                ("the-345-hat-corduroy-dot-v2", "Black"),
                ("the-345-hat-corduroy-dot-v2", "Brown"),
                ("the-345-hat-corduroy-dot-v2", "Burgundy"),
                ("the-345-hat-corduroy-dot-v2", "Olive"),
            ],
            "roman": [
                ("the-345-hat-corduroy-roman-v2", "Black"),
                ("the-345-hat-corduroy-roman-v2", "Brown"),
                ("the-345-hat-corduroy-roman-v2", "Burgundy"),
                ("the-345-hat-corduroy-roman-v2", "Olive"),
            ],
        },
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
    "sweats": ["unisex fit, true to size", "sizes xs to 2xl", "machine wash cold, hang dry to protect the embroidery"],
    "oversized-sweats": ["relaxed fit by design: size down for a closer fit", "sizes s to 3xl", "machine wash cold, hang dry"],
    "tee-mens": ["regular to boxy fit, true to size", "machine wash cold, tumble low"],
    "tee-womens": ["longline fit, sizes S to L only", "machine wash cold, tumble low"],
    "beanie": ["one size fits most", "hand wash, lay flat to dry"],
    "hat-distressed": ["one size, adjustable hook and loop closure", "distressing varies piece to piece, that is the point", "spot clean"],
    "hat-denim": ["one size, adjustable strap", "pigment dye softens and fades with wear", "spot clean"],
    "hat-corduroy": ["one size, adjustable strap with a metal buckle", "fits heads 20 to 22 inches", "spot clean"],
    "blanket": ["50 x 60 inches", "machine wash cold, tumble low", "ships in its own box"],
}
SHARED_KNOW = ["made to order, one at a time, by our print partner printful", "ships from the us, usually 5 to 9 business days door to door", "wrong size or a flaw in the print: send us a note from the support page within 30 days and we will make it right"]

# printful's hat mockups sit smaller in their frame than the garments; scale them so every
# tile reads the same size (measured: garments fill ~95% of the mockup, hats ~79%).
ZOOM = {"beanie": 1.19, "hat-distressed": 1.19, "hat-denim": 1.19, "hat-corduroy": 1.19}
# mockups that are not transparent: blend their near-white background into the tile
BLEND = {"hat-denim"}

STORE = "https://345loveyours.printful.me"
# What each piece costs us at Printful (base sizes / plus sizes), from the Oct 2026 pricing audit.
# Used for the ledger (what goes to the partner) and for the at-cost promo code.
COST = {
    "hoodie": (36.83, 40.83), "oversized-hoodie": (42.22, 46.22), "crewneck": (33.23, 37.23),
    "sweats": (30.04, 32.04), "oversized-sweats": (39.27, 43.27),
    "tee-mens": (24.17, 28.17), "tee-womens": (21.73, 21.73), "beanie": (16.51, 16.51),
    "hat-distressed": (19.00, 19.00), "hat-denim": (19.86, 19.86), "hat-corduroy": (19.26, 19.26),
    "blanket": (46.82, 46.82),
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
    style_entries = [("classic", e) for e in p["colors"]] + [(sid, e) for sid, _ in STYLES[1:] for e in p.get("styles", {}).get(sid, [])]
    for sid, entry in style_entries:
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
            "style": sid,
            "styleLabel": dict(STYLES)[sid],
            "hex": c["hex"],
            "tag": tag,
            "printful": f"{STORE}/product/{slug}",
            "listing": src["name"],
            "images": reorder_mocks(src["pid"], c["mocks"], src["id"]),
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
        "styles": [{"id": sid, "label": label} for sid, label in STYLES if any(c["style"] == sid for c in colors)],
        "styleCopy": {sid: {"line": STYLE_LINE[sid], "intro": restyle(p["intro"], label), "note": restyle(p["note"], label), "placement": restyle(p["placement"], label)}
                      for sid, label in STYLES if any(c["style"] == sid for c in colors)},
        "colors": colors,
    })

(ROOT / "data/products.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
n_colors = sum(len(p["colors"]) for p in out)
n_var = sum(len(c["sizes"]) for p in out for c in p["colors"])
print(f"wrote {len(out)} products, {n_colors} colourways, {n_var} variants")
