/* 3|4|5 site script. Renders header, footer, shop grid, product page and bag
   from data/products.json. Edit copy in the HTML, products in tools/build-products.py. */
(function () {
  'use strict';

  var CONFIG = {
    // Where product images come from. Printful CDN for now; run tools/fetch-images.sh
    // and change this to 'img/' to self-host them.
    imgBase: 'https://cdn.printful.me/t/quick-stores/variants/',
    imgGrid: function (id) { if (window.PREVIEW_IMG && window.PREVIEW_IMG[id]) return window.PREVIEW_IMG[id]; return CONFIG.imgBase.indexOf('http') === 0 ? CONFIG.imgBase + 'w339/' + id + '__825' : CONFIG.imgBase + id + '.png'; },
    imgFull: function (id) { if (window.PREVIEW_IMG && window.PREVIEW_IMG[id]) return window.PREVIEW_IMG[id]; return CONFIG.imgBase.indexOf('http') === 0 ? CONFIG.imgBase + id : CONFIG.imgBase + id + '.png'; },
    store: 'https://345loveyours.printful.me',
    // The checkout worker (Cloudflare). Set after `wrangler deploy` prints the URL.
    checkoutUrl: 'https://ily345-checkout.ceokrone.workers.dev',
    supportEmail: 'support345@gmail.com',
    showGridPrice: true,
    featured: [['hoodie', 'Black'], ['oversized-hoodie', 'Vintage Brown'], ['crewneck', 'Latte']],
    heroImage: '1076503569082fa8eff33', // black hoodie, back (the message)
    storyImage: '1076511469083056abb20', // white hoodie, back: contrast on the espresso band
    groups: [
      { title: 'hoodies and sweatshirts', cats: ['hoodies', 'sweatshirts'] },
      { title: 'tees', cats: ['tees'] },
      { title: 'hats', cats: ['hats'] },
      { title: 'home', cats: ['home'] }
    ],
    bagKey: 'ily345-bag'
  };

  var page = document.body.getAttribute('data-page') || '';
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  var money = function (n) { return '$' + n; };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var priceLabel = function (p) { return p.price === p.priceMax ? money(p.price) : 'from ' + money(p.price); };

  /* ---------- bag store (localStorage) ---------- */
  var Bag = {
    read: function () { if (window.PREVIEW_BAG) return window.PREVIEW_BAG; try { return JSON.parse(localStorage.getItem(CONFIG.bagKey)) || []; } catch (e) { return []; } },
    write: function (items) { if (window.PREVIEW_BAG) window.PREVIEW_BAG = items; try { localStorage.setItem(CONFIG.bagKey, JSON.stringify(items)); } catch (e) {} renderBagCount(); },
    add: function (line) {
      var items = Bag.read();
      var hit = items.filter(function (i) { return i.variant === line.variant; })[0];
      if (hit) hit.qty += line.qty; else items.push(line);
      Bag.write(items);
    },
    setQty: function (variant, qty) {
      var items = Bag.read().map(function (i) { if (i.variant === variant) i.qty = qty; return i; }).filter(function (i) { return i.qty > 0; });
      Bag.write(items);
    },
    count: function () { return Bag.read().reduce(function (n, i) { return n + i.qty; }, 0); },
    subtotal: function () { return Bag.read().reduce(function (n, i) { return n + i.qty * i.price; }, 0); }
  };

  /* ---------- header + footer ---------- */
  function renderChrome() {
    var h = $('#site-header');
    if (h) {
      h.className = 'site-header';
      h.innerHTML =
        '<div class="wrap header-row">' +
          '<nav class="nav label" aria-label="primary">' +
            '<a href="index.html#shop"' + (page === 'shop' || page === 'product' ? ' aria-current="page"' : '') + '>shop</a>' +
            '<a href="story.html" class="hide-sm"' + (page === 'story' ? ' aria-current="page"' : '') + '>story</a>' +
            '<a href="send.html" class="hide-sm"' + (page === 'send' ? ' aria-current="page"' : '') + '>send a 345</a>' +
          '</nav>' +
          '<a class="wordmark" href="index.html" aria-label="3 4 5 home">3 | 4 | 5</a>' +
          '<nav class="nav right label" aria-label="bag">' +
            '<a href="index.html#details" class="hide-sm">good to know</a>' +
            '<a href="bag.html"' + (page === 'bag' ? ' aria-current="page"' : '') + '>bag <span class="bag-count" id="bag-count">(0)</span></a>' +
          '</nav>' +
        '</div>';
    }
    var f = $('#site-footer');
    if (f) {
      f.className = 'site-footer';
      f.innerHTML =
        '<div class="wrap footer-row label muted">' +
          '<div>3 | 4 | 5 · love yours.</div>' +
          '<nav class="nav" aria-label="footer">' +
            '<a href="index.html#shop">shop</a>' +
            '<a href="story.html">story</a>' +
            '<a href="send.html">send a 345</a>' +
            '<a href="index.html#details">good to know</a>' +
            '<a href="mailto:' + CONFIG.supportEmail + '">' + CONFIG.supportEmail + '</a>' +
          '</nav>' +
          '<div>story first · product second</div>' +
        '</div>';
    }
    renderBagCount();
  }
  function renderBagCount() {
    var el = $('#bag-count');
    if (el) el.textContent = '(' + Bag.count() + ')';
  }

  /* ---------- products ---------- */
  function loadProducts(cb) {
    if (window.PRODUCTS) return cb(window.PRODUCTS);
    fetch('data/products.json?v=26e9fe0d').then(function (r) { return r.json(); }).then(function (d) { window.PRODUCTS = d; cb(d); })
      .catch(function () { var el = $('[data-products-error]'); if (el) el.hidden = false; });
  }
  function findProduct(list, id) { return list.filter(function (p) { return p.id === id; })[0]; }

  function tileHTML(p, colorName) {
    if (typeof colorName !== 'string') colorName = null;
    var c = p.colors.filter(function (x) { return x.name === colorName; })[0] || p.colors[0];
    var front = c.images[0], back = c.images[1];
    var cover = (p.opaque ? (p.fill ? ' cover' : ' flat') + '" style="background:' + p.opaque : '') + (p.blend ? ' blend' : '');
    var href = 'product.html?p=' + p.id + (colorName ? '&c=' + encodeURIComponent(c.name) : '');
    var chips = p.colors.map(function (x) {
      return '<span class="chip" style="background:' + x.hex + '" title="' + esc(x.name) + '"></span>';
    }).join('');
    return '<a class="tile reveal' + (back ? ' has-alt' : '') + '" href="' + href + '">' +
      '<div class="tile-visual' + cover + '"' + (p.zoom && p.zoom !== 1 ? ' style="--zoom:' + p.zoom + '"' : '') + '>' +
        '<img src="' + CONFIG.imgGrid(front) + '" alt="' + esc(p.name) + ', ' + esc(c.name) + '" loading="lazy">' +
        (back ? '<img class="alt" src="' + CONFIG.imgGrid(back) + '" alt="" loading="lazy">' : '') +
      '</div>' +
      '<div class="tile-meta">' +
        '<div class="tile-name">' + esc(p.name) + '</div>' +
        '<div class="tile-sub label muted">' +
          '<span class="chips" title="' + p.colors.length + (p.colors.length === 1 ? ' color' : ' colors') + '" aria-label="' + p.colors.length + ' colors">' + chips + '</span>' +
          (CONFIG.showGridPrice ? '<span>' + priceLabel(p) + '</span>' : '') +
        '</div>' +
      '</div>' +
    '</a>';
  }

  /* ---------- home ---------- */
  function initHome(list) {
    var grid = $('#featured');
    if (grid) grid.innerHTML = CONFIG.featured.map(function (f) { var p = findProduct(list, f[0]); return p ? tileHTML(p, f[1]) : ''; }).join('');
    var hero = $('#hero-img');
    if (hero) { hero.src = CONFIG.imgFull(CONFIG.heroImage); hero.alt = 'the 345 hoodie, back: i love you. i believe in you. i am proud of you.'; }
    var cat = $('#catalog');
    if (cat) {
      cat.innerHTML = CONFIG.groups.map(function (g) {
        var items = list.filter(function (p) { return g.cats.indexOf(p.category) >= 0; });
        if (!items.length) return '';
        return '<section class="cat"><div class="wrap">' +
          '<div class="section-head"><h2 class="label">' + esc(g.title) + '</h2><span class="label cat-count">' + items.length + (items.length === 1 ? ' piece' : ' pieces') + '</span></div>' +
          '<div class="grid">' + items.map(tileHTML).join('') + '</div>' +
        '</div></section>';
      }).join('');
    }
    observeReveal();
  }

  /* ---------- shop ---------- */
  function initShop(list) {
    var grid = $('#grid'), filters = $('#filters');
    var cats = [];
    list.forEach(function (p) { if (cats.indexOf(p.category) < 0) cats.push(p.category); });
    var current = (location.hash || '').replace('#', '') || 'all';
    function draw() {
      grid.innerHTML = list.filter(function (p) { return current === 'all' || p.category === current; }).map(tileHTML).join('');
      $$('button', filters).forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-cat') === current ? 'true' : 'false'); });
      observeReveal();
    }
    filters.innerHTML = ['all'].concat(cats).map(function (c) { return '<button class="label" data-cat="' + c + '">' + c + '</button>'; }).join('');
    filters.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      current = b.getAttribute('data-cat'); history.replaceState(null, '', current === 'all' ? location.pathname : '#' + current); draw();
    });
    draw();
  }

  /* ---------- product ---------- */
  function initProduct(list) {
    var id = new URLSearchParams(location.search).get('p') || window.PREVIEW_PRODUCT;
    var p = findProduct(list, id) || list[0];
    var state = { color: 0, size: null, image: 0 };
    var ci = new URLSearchParams(location.search).get('c');
    if (ci) { var idx = p.colors.map(function (c) { return c.name.toLowerCase(); }).indexOf(ci.toLowerCase()); if (idx >= 0) state.color = idx; }
    document.title = p.name + ' · 3 | 4 | 5';
    var cover = (p.opaque ? (p.fill ? ' cover' : ' flat') + '" style="background:' + p.opaque : '') + (p.blend ? ' blend' : '');
    var root = $('#pdp');
    root.innerHTML =
      '<div class="pdp-gallery">' +
        '<div class="pdp-main' + cover + '"' + (p.zoom && p.zoom !== 1 ? ' style="--zoom:' + p.zoom + '"' : '') + '><img id="pdp-img" alt=""></div>' +
        '<div class="thumbs" id="thumbs"></div>' +
      '</div>' +
      '<div class="pdp-info">' +
        '<div class="pdp-title">' +
          '<div class="label accent">' + esc(p.short) + '</div>' +
          '<h1 class="display-sm">' + esc(p.name) + '</h1>' +
          '<div class="pdp-price" id="pdp-price"></div>' +
        '</div>' +
        '<div class="opt"><div class="opt-head label"><span>color</span><span class="muted" id="color-name"></span></div><div class="color-list" id="colors"></div></div>' +
        '<div class="opt" id="size-opt"><div class="opt-head label"><span>size</span><span class="muted" id="fit-hint"></span></div><div class="size-list" id="sizes"></div></div>' +
        '<div class="pdp-actions">' +
          '<button class="btn full" id="add">add to bag</button>' +
          '<div class="pdp-hint">made to order and shipped from the us, usually 5 to 9 business days. secure checkout by stripe.</div>' +
        '</div>' +
        '<div class="acc">' +
          '<details open><summary class="label">about</summary><div class="acc-body prose"><p>' + esc(p.intro) + '</p><p>' + esc(p.note) + '</p></div></details>' +
          '<details><summary class="label">the message</summary><div class="acc-body prose">' + p.message.map(function (m) { return '<p>' + esc(m) + '</p>'; }).join('') + '</div></details>' +
          '<details><summary class="label">materials</summary><div class="acc-body"><ul>' + p.details.map(function (d) { return '<li>' + esc(d) + '</li>'; }).join('') + '</ul></div></details>' +
          '<details><summary class="label">good to know</summary><div class="acc-body"><ul class="know">' + p.know.map(function (d) { return '<li>' + esc(d) + '</li>'; }).join('') + '</ul></div></details>' +
        '</div>' +
      '</div>';

    var img = $('#pdp-img'), thumbs = $('#thumbs'), colors = $('#colors'), sizes = $('#sizes'), price = $('#pdp-price');
    $('#fit-hint').textContent = (p.know && p.know[0]) ? p.know[0] : '';
    function color() { return p.colors[state.color]; }
    function drawColors() {
      colors.innerHTML = p.colors.map(function (c, i) {
        return '<button style="background:' + c.hex + '" title="' + esc(c.name) + (c.tag ? ' (' + c.tag + ')' : '') + '" aria-label="' + esc(c.name) + '" aria-pressed="' + (i === state.color) + '" data-i="' + i + '"></button>';
      }).join('');
      $('#color-name').textContent = color().name.toLowerCase() + (color().tag ? ' · ' + color().tag : '');
    }
    function drawImages() {
      var c = color();
      state.image = Math.min(state.image, c.images.length - 1);
      img.src = CONFIG.imgFull(c.images[state.image]);
      img.alt = p.name + ', ' + c.name;
      thumbs.innerHTML = c.images.map(function (m, i) {
        return '<button aria-pressed="' + (i === state.image) + '" data-i="' + i + '" aria-label="view ' + (i + 1) + '"><img src="' + CONFIG.imgGrid(m) + '" alt=""></button>';
      }).join('');
    }
    function drawSizes() {
      var c = color();
      var single = c.sizes.length === 1;
      if (single) state.size = c.sizes[0].size;
      $('#size-opt').hidden = single && c.sizes[0].size === 'One size';
      sizes.innerHTML = c.sizes.map(function (s) {
        return '<button aria-pressed="' + (s.size === state.size) + '" data-size="' + esc(s.size) + '">' + esc(s.size) + '</button>';
      }).join('');
      var sel = c.sizes.filter(function (s) { return s.size === state.size; })[0];
      price.textContent = sel ? money(sel.price) : priceLabel(p);
    }
    colors.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      state.color = +b.getAttribute('data-i');
      var keep = color().sizes.some(function (s) { return s.size === state.size; });
      if (!keep) state.size = null;
      drawColors(); drawImages(); drawSizes();
      history.replaceState(null, '', '?p=' + p.id + '&c=' + encodeURIComponent(color().name));
    });
    thumbs.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; state.image = +b.getAttribute('data-i'); drawImages(); });
    sizes.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; state.size = b.getAttribute('data-size'); drawSizes(); });
    $('#add').addEventListener('click', function () {
      var c = color();
      if (!state.size) { sizes.style.outline = '1px solid var(--ink)'; sizes.style.outlineOffset = '6px'; setTimeout(function () { sizes.style.outline = ''; }, 1200); return; }
      var s = c.sizes.filter(function (x) { return x.size === state.size; })[0];
      Bag.add({ variant: s.variant, product: p.id, name: p.name, color: c.name, size: s.size, price: s.price, qty: 1, image: c.images[0], printful: c.printful, listing: c.listing, cover: p.opaque || false, fill: !!p.fill });
      var btn = $('#add'); btn.textContent = 'added · view bag'; btn.onclick = function () { location.href = 'bag.html'; };
    });
    drawColors(); drawImages(); drawSizes();

    var more = $('#more');
    if (more) more.innerHTML = list.filter(function (x) { return x.id !== p.id; }).slice(0, 4).map(tileHTML).join('');
    observeReveal();
  }

  /* ---------- bag ---------- */
  function initBag() {
    var lines = $('#bag-lines'), summary = $('#bag-summary'), empty = $('#bag-empty'), layout = $('#bag-layout');
    function draw() {
      var items = Bag.read();
      var has = items.length > 0;
      layout.hidden = !has; empty.hidden = has;
      if (!has) return;
      lines.innerHTML = items.map(function (i) {
        return '<div class="bag-line">' +
          '<a class="bag-thumb' + (i.cover ? (i.fill ? ' cover' : ' flat') + '" style="background:' + i.cover : '') + '" href="product.html?p=' + i.product + '&c=' + encodeURIComponent(i.color) + '"><img src="' + CONFIG.imgGrid(i.image) + '" alt=""></a>' +
          '<div class="bag-info">' +
            '<div class="small">' + esc(i.name) + '</div>' +
            '<div class="label muted">' + esc(i.color.toLowerCase()) + (i.size && i.size !== 'One size' ? ' · ' + esc(i.size) : '') + '</div>' +
            '<div class="qty"><button data-v="' + i.variant + '" data-d="-1" aria-label="less">–</button><span>' + i.qty + '</span><button data-v="' + i.variant + '" data-d="1" aria-label="more">+</button></div>' +
          '</div>' +
          '<div class="bag-right">' +
            '<div class="small">' + money(i.price * i.qty) + '</div>' +
            '<button class="label muted link-u" data-v="' + i.variant + '" data-d="-99">remove</button>' +
          '</div>' +
        '</div>';
      }).join('');
      var sub = Bag.subtotal();
      summary.innerHTML =
        '<div class="label">summary</div>' +
        '<div class="sum-row"><span class="muted">items</span><span>' + Bag.count() + '</span></div>' +
        '<div class="sum-row"><span class="muted">shipping</span><span class="muted">at checkout</span></div>' +
        '<div class="sum-row total"><span>subtotal</span><span>' + money(sub) + '</span></div>' +
        '<button class="btn full" id="checkout">checkout</button>' +
        '<div class="pdp-hint" id="checkout-hint">secure checkout by stripe. apple pay, google pay and cards. us shipping. sending it as a gift? you can add a note at checkout and we print it inside the box.</div>';
      $('#checkout').addEventListener('click', startCheckout);
    }
    lines.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-v]'); if (!b) return;
      var v = +b.getAttribute('data-v'), d = +b.getAttribute('data-d');
      var item = Bag.read().filter(function (i) { return i.variant === v; })[0];
      Bag.setQty(v, d === -99 ? 0 : item.qty + d); draw();
    });
    draw();
  }

  function startCheckout() {
    var btn = $('#checkout'), hint = $('#checkout-hint');
    var items = Bag.read().map(function (i) { return { variant: i.variant, qty: i.qty }; });
    if (!items.length) return;
    if (CONFIG.checkoutUrl.indexOf('REPLACE-ME') > -1) {
      hint.textContent = 'checkout opens shortly. until then, email your bag to ' + CONFIG.supportEmail + ' and we will send a payment link.';
      return;
    }
    btn.disabled = true; btn.textContent = 'one moment';
    fetch(CONFIG.checkoutUrl + '/checkout', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ items: items }) })
      .then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.error || 'checkout failed'); return d; }); })
      .then(function (d) { location.href = d.url; })
      .catch(function (e) {
        btn.disabled = false; btn.textContent = 'checkout';
        hint.textContent = 'checkout could not start (' + e.message + '). try again, or write to ' + CONFIG.supportEmail + '.';
      });
  }

  /* ---------- thanks ---------- */
  function initThanks() {
    var sid = new URLSearchParams(location.search).get('session_id');
    if (sid) { try { localStorage.removeItem(CONFIG.bagKey); } catch (e) {} renderBagCount(); }
  }

  /* ---------- send a 345: a card drawn on canvas, shareable by link or image ---------- */
  function initSend() {
    var cv = $('#send-canvas'); if (!cv) return;
    var ctx = cv.getContext('2d');
    var MEAN = { '3': 'i love you.', '4': 'i believe in you.', '5': 'i am proud of you.', '345': 'i love you. i believe in you. i am proud of you.' };
    var TONES = {
      stone: { bg: '#e9e7e1', ink: '#171717', muted: '#7a7873', accent: '#8a6a4e' },
      espresso: { bg: '#2b221c', ink: '#f1ebe4', muted: '#b39c86', accent: '#c9b39b' },
      latte: { bg: '#b28a68', ink: '#1f1915', muted: '#5a4737', accent: '#f1ebe4' },
      black: { bg: '#171717', ink: '#f1efea', muted: '#9a9790', accent: '#c9b39b' }
    };
    var q = new URLSearchParams(location.search);
    var state = { n: MEAN[q.get('n')] ? q.get('n') : '3', to: (q.get('to') || '').slice(0, 24), from: (q.get('from') || '').slice(0, 24), tone: TONES[q.get('tone')] ? q.get('tone') : 'stone' };
    $('#send-to').value = state.to; $('#send-from').value = state.from;

    function line(text, x, y, font, color, align) { ctx.font = font; ctx.fillStyle = color; ctx.textAlign = align || 'left'; ctx.fillText(text, x, y); }
    function wrap(text, x, y, maxW, lh, font, color) {
      ctx.font = font; ctx.fillStyle = color; ctx.textAlign = 'left';
      var words = text.split(' '), cur = '', lines = [];
      words.forEach(function (w) { var t = cur ? cur + ' ' + w : w; if (ctx.measureText(t).width > maxW && cur) { lines.push(cur); cur = w; } else cur = t; });
      if (cur) lines.push(cur);
      lines.forEach(function (l, i) { ctx.fillText(l, x, y + i * lh); });
      return y + lines.length * lh;
    }
    function draw() {
      var t = TONES[state.tone], W = cv.width, H = cv.height, m = 96;
      ctx.clearRect(0, 0, W, H); ctx.fillStyle = t.bg; ctx.fillRect(0, 0, W, H);
      ctx.strokeStyle = t.accent; ctx.lineWidth = 2; ctx.strokeRect(40, 40, W - 80, H - 80);
      line('3  |  4  |  5', m, 160, '500 26px -apple-system, Helvetica, Arial, sans-serif', t.accent);
      if (state.to) line('for ' + state.to.toLowerCase(), W - m, 160, '500 26px -apple-system, Helvetica, Arial, sans-serif', t.muted, 'right');
      var big = state.n === '345' ? '3 | 4 | 5' : state.n;
      line(big, W / 2, state.n === '345' ? 640 : 700, (state.n === '345' ? '300 300px' : '300 520px') + ' Georgia, "Times New Roman", serif', t.ink, 'center');
      var y = wrap(MEAN[state.n], m, 880, W - 2 * m, 72, '400 56px Georgia, "Times New Roman", serif', t.ink);
      if (state.from) line('from ' + state.from.toLowerCase(), m, y + 40, '500 26px -apple-system, Helvetica, Arial, sans-serif', t.muted);
      line('3 | i love you.  4 | i believe in you.  5 | i am proud of you.', m, H - 150, '400 22px -apple-system, Helvetica, Arial, sans-serif', t.muted);
      line('ily345.com  ·  love yours.', m, H - 108, '500 22px -apple-system, Helvetica, Arial, sans-serif', t.accent);
      $('#send-meaning').textContent = MEAN[state.n].replace(/\.$/, '');
      $('#send-tone-name').textContent = state.tone;
      $$('#send-nums button').forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-n') === state.n); });
      $$('#send-tones button').forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-tone') === state.tone); });
      var u = new URLSearchParams(); u.set('n', state.n); if (state.to) u.set('to', state.to); if (state.from) u.set('from', state.from); if (state.tone !== 'stone') u.set('tone', state.tone);
      try { history.replaceState(null, '', 'send.html?' + u.toString()); } catch (e) {}
    }
    function shareUrl() { return 'https://ily345.com/' + location.pathname.split('/').pop() + location.search; }
    function hint(msg) { var h = $('#send-hint'); h.textContent = msg; }
    $('#send-nums').addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; state.n = b.getAttribute('data-n'); draw(); });
    $('#send-tones').addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; state.tone = b.getAttribute('data-tone'); draw(); });
    $('#send-to').addEventListener('input', function (e) { state.to = e.target.value.slice(0, 24); draw(); });
    $('#send-from').addEventListener('input', function (e) { state.from = e.target.value.slice(0, 24); draw(); });
    $('#send-copy').addEventListener('click', function () {
      var u = shareUrl();
      (navigator.clipboard ? navigator.clipboard.writeText(u) : Promise.reject()).then(function () { hint('link copied. paste it in a text and they will open this exact card.'); }, function () { hint('copy this: ' + u); });
    });
    $('#send-save').addEventListener('click', function () {
      var a = document.createElement('a'); a.download = '345-' + state.n + (state.to ? '-' + state.to.toLowerCase().replace(/[^a-z0-9]+/g, '-') : '') + '.png'; a.href = cv.toDataURL('image/png'); a.click();
      hint('saved. drop it in a text, a story, or print it.');
    });
    $('#send-share').addEventListener('click', function () {
      var text = (state.n === '345' ? '3 4 5' : state.n) + '. ' + MEAN[state.n] + (state.from ? ' from ' + state.from : '');
      if (navigator.share) {
        cv.toBlob(function (blob) {
          var file = blob && typeof File !== 'undefined' ? new File([blob], '345.png', { type: 'image/png' }) : null;
          var data = { title: 'send a 345', text: text, url: shareUrl() };
          if (file && navigator.canShare && navigator.canShare({ files: [file] })) data.files = [file];
          navigator.share(data).catch(function () {});
        });
      } else { $('#send-copy').click(); }
    });
    draw();
  }

  /* ---------- back to top (appears after the first screen) ---------- */
  function initTop() {
    var b = document.createElement('button'); b.className = 'to-top label'; b.textContent = 'top'; b.setAttribute('aria-label', 'back to top'); b.hidden = true;
    b.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
    document.body.appendChild(b);
    var last = 0;
    window.addEventListener('scroll', function () { var y = window.scrollY; var show = y > window.innerHeight * 1.5; if (show !== !b.hidden) b.hidden = !show; last = y; }, { passive: true });
  }

  /* ---------- reveal ---------- */
  function observeReveal() {
    if (!('IntersectionObserver' in window)) { $$('.reveal').forEach(function (el) { el.classList.add('in'); }); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { threshold: 0.08 });
    $$('.reveal:not(.in)').forEach(function (el) { io.observe(el); });
  }

  /* ---------- boot ---------- */
  renderChrome();
  initTop();
  observeReveal();
  if (page === 'home') loadProducts(initHome);
  if (page === 'shop') loadProducts(initShop);
  if (page === 'product') loadProducts(initProduct);
  if (page === 'bag') initBag();
  if (page === 'thanks') initThanks();
  if (page === 'send') initSend();
  if (page === 'story') { var si = $('#story-img'); if (si) si.src = CONFIG.imgFull(CONFIG.storyImage); observeReveal(); }
})();
