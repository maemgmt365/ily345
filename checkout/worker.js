/*
  ily345 checkout worker (Cloudflare Workers, no dependencies).

  POST /checkout   { items: [{ variant: <printful sync variant id>, qty: n }], email? }
                   -> creates a Stripe Checkout Session (hosted page) with the real
                      Printful shipping rate for the US and returns { url }.
  POST /webhook    Stripe -> checkout.session.completed -> creates and confirms the
                   Printful order for the paid session.
  GET  /health     -> "ok" plus which config is present.

  Secrets (wrangler secret put):  STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, PRINTFUL_TOKEN
  Vars (wrangler.toml):           SITE_ORIGIN, PRINTFUL_STORE_ID, SUPPORT_EMAIL, STRIPE_TAX ("on"/"off")

  Money is handled in integer cents everywhere.
*/

const CATALOG_URL_PATH = '/data/products.json';
const PF = 'https://api.printful.com';
const STRIPE = 'https://api.stripe.com/v1';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const cors = corsHeaders(request, env);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });

    try {
      if (url.pathname === '/health') {
        return json({ ok: true, stripe: !!env.STRIPE_SECRET_KEY, printful: !!env.PRINTFUL_TOKEN, webhook: !!env.STRIPE_WEBHOOK_SECRET, store: env.PRINTFUL_STORE_ID || null }, 200, cors);
      }
      if (url.pathname === '/checkout' && request.method === 'POST') {
        return await createCheckout(request, env, cors);
      }
      if (url.pathname === '/webhook' && request.method === 'POST') {
        return await handleWebhook(request, env, ctx);
      }
      return json({ error: 'not found' }, 404, cors);
    } catch (err) {
      console.error('worker error', err && err.stack || err);
      return json({ error: String(err && err.message || err) }, 500, cors);
    }
  }
};

/* ---------------- checkout ---------------- */

async function createCheckout(request, env, cors) {
  const body = await request.json().catch(() => ({}));
  const wanted = Array.isArray(body.items) ? body.items : [];
  if (!wanted.length) return json({ error: 'empty bag' }, 400, cors);

  // Price every line from the site's own catalog, never from the client.
  const catalog = await loadCatalog(env);
  const lines = [];
  for (const w of wanted) {
    const v = catalog.byVariant[String(w.variant)];
    const qty = Math.max(1, Math.min(10, parseInt(w.qty, 10) || 1));
    if (!v) return json({ error: 'unknown item ' + w.variant }, 400, cors);
    lines.push({ ...v, qty });
  }

  // Real Printful shipping rate for a US address (Printful's US rates are flat by product).
  const shipping = await printfulShippingRate(env, lines);

  const origin = env.SITE_ORIGIN || 'https://ily345.com';
  const form = new URLSearchParams();
  form.set('mode', 'payment');
  form.set('success_url', origin + '/thanks.html?session_id={CHECKOUT_SESSION_ID}');
  form.set('cancel_url', origin + '/bag.html');
  form.set('shipping_address_collection[allowed_countries][0]', 'US');
  form.set('phone_number_collection[enabled]', 'true');
  form.set('billing_address_collection', 'auto');
  form.set('allow_promotion_codes', 'false');
  if (body.email) form.set('customer_email', String(body.email).slice(0, 200));
  if ((env.STRIPE_TAX || 'off') === 'on') form.set('automatic_tax[enabled]', 'true');

  // Gift note: optional, printed on the packing slip inside the box.
  form.set('custom_fields[0][key]', 'gift_note');
  form.set('custom_fields[0][label][type]', 'custom');
  form.set('custom_fields[0][label][custom]', 'gift note (printed inside the box)');
  form.set('custom_fields[0][type]', 'text');
  form.set('custom_fields[0][optional]', 'true');
  form.set('custom_fields[0][text][maximum_length]', '140');

  lines.forEach((l, i) => {
    const p = `line_items[${i}]`;
    form.set(`${p}[quantity]`, String(l.qty));
    form.set(`${p}[price_data][currency]`, 'usd');
    form.set(`${p}[price_data][unit_amount]`, String(l.priceCents));
    form.set(`${p}[price_data][product_data][name]`, l.name);
    form.set(`${p}[price_data][product_data][description]`, [l.color, l.size].filter(Boolean).join(' · '));
    if (l.image) form.set(`${p}[price_data][product_data][images][0]`, l.image);
    form.set(`${p}[price_data][product_data][metadata][variant]`, String(l.variant));
    if ((env.STRIPE_TAX || 'off') === 'on') form.set(`${p}[price_data][tax_behavior]`, 'exclusive');
  });

  form.set('shipping_options[0][shipping_rate_data][type]', 'fixed_amount');
  form.set('shipping_options[0][shipping_rate_data][fixed_amount][amount]', String(shipping.cents));
  form.set('shipping_options[0][shipping_rate_data][fixed_amount][currency]', 'usd');
  form.set('shipping_options[0][shipping_rate_data][display_name]', shipping.name);
  if (shipping.minDays) {
    form.set('shipping_options[0][shipping_rate_data][delivery_estimate][minimum][unit]', 'business_day');
    form.set('shipping_options[0][shipping_rate_data][delivery_estimate][minimum][value]', String(shipping.minDays));
    form.set('shipping_options[0][shipping_rate_data][delivery_estimate][maximum][unit]', 'business_day');
    form.set('shipping_options[0][shipping_rate_data][delivery_estimate][maximum][value]', String(shipping.maxDays));
  }
  if ((env.STRIPE_TAX || 'off') === 'on') form.set('shipping_options[0][shipping_rate_data][tax_behavior]', 'exclusive');

  // What the webhook needs to place the Printful order. Kept tiny to fit metadata limits.
  form.set('metadata[items]', JSON.stringify(lines.map(l => [l.catalogVariant, l.qty, l.template])));
  form.set('metadata[shipping_cents]', String(shipping.cents));
  form.set('metadata[source]', 'ily345.com');

  const session = await stripe(env, 'POST', '/checkout/sessions', form);
  return json({ url: session.url, id: session.id }, 200, cors);
}

async function printfulShippingRate(env, lines) {
  // Printful needs a recipient to quote. US rates are flat per product type, so a fixed
  // US address gives the right number before Stripe collects the real one.
  const payload = {
    recipient: { address1: '100 Congress Ave', city: 'Austin', state_code: 'TX', country_code: 'US', zip: '78701' },
    items: lines.map(l => ({ variant_id: l.catalogVariant, quantity: l.qty })),
    currency: 'USD',
    locale: 'en_US'
  };
  try {
    const res = await printful(env, 'POST', '/shipping/rates', payload);
    const rates = (res && res.result) || [];
    const std = rates.find(r => r.id === 'STANDARD') || rates[0];
    if (std) {
      return { cents: Math.round(parseFloat(std.rate) * 100), name: 'standard shipping', minDays: std.minDeliveryDays || null, maxDays: std.maxDeliveryDays || null };
    }
  } catch (e) {
    console.error('printful rate failed, using fallback', e && e.message);
  }
  // Fallback if Printful is unreachable: their usual US flat rate for one apparel item.
  return { cents: 599, name: 'standard shipping', minDays: 5, maxDays: 9 };
}

/* ---------------- webhook ---------------- */

async function handleWebhook(request, env, ctx) {
  const raw = await request.text();
  const sig = request.headers.get('stripe-signature') || '';
  const ok = await verifyStripeSignature(raw, sig, env.STRIPE_WEBHOOK_SECRET);
  if (!ok) return new Response('bad signature', { status: 400 });

  const event = JSON.parse(raw);
  if (event.type !== 'checkout.session.completed') return new Response('ignored', { status: 200 });

  const session = event.data.object;
  if (session.payment_status !== 'paid') return new Response('not paid', { status: 200 });

  // Idempotency: Printful rejects a duplicate external_id, so a retried webhook is safe.
  const items = JSON.parse((session.metadata && session.metadata.items) || '[]');
  const ship = (session.collected_information && session.collected_information.shipping_details) || session.shipping_details || {};
  const addr = ship.address || {};
  const details = session.customer_details || {};

  const order = {
    external_id: session.id,
    shipping: 'STANDARD',
    recipient: {
      name: ship.name || details.name || 'ily345 customer',
      address1: addr.line1 || '',
      address2: addr.line2 || '',
      city: addr.city || '',
      state_code: addr.state || '',
      country_code: addr.country || 'US',
      zip: addr.postal_code || '',
      phone: details.phone || '',
      email: details.email || ''
    },
    // catalog variant + the product template that holds the design (quick stores have no API).
    items: items.map(([variant, qty, template]) => ({ variant_id: Number(variant), product_template_id: Number(template), quantity: Number(qty) })),
    retail_costs: {
      currency: 'USD',
      subtotal: cents(session.amount_subtotal),
      shipping: cents(Number(session.metadata && session.metadata.shipping_cents) || 0),
      tax: cents((session.total_details && session.total_details.amount_tax) || 0),
      total: cents(session.amount_total)
    },
    packing_slip: {
      email: env.SUPPORT_EMAIL || '',
      message: giftNote(session) || 'i love you. i believe in you. i am proud of you. love yours.',
      store_name: '3 | 4 | 5'
    }
  };

  // PRINTFUL_CONFIRM=on submits for fulfilment right away (charges your Printful wallet/card).
  // Anything else leaves it as a draft you confirm by hand in the Printful dashboard.
  const confirm = (env.PRINTFUL_CONFIRM || 'off') === 'on';
  const res = await printful(env, 'POST', '/orders' + (confirm ? '?confirm=true' : ''), order);
  console.log('printful order', res && res.result && res.result.id, 'for', session.id);
  return new Response('ok', { status: 200 });
}

/* ---------------- helpers ---------------- */

// The optional gift note typed at checkout, trimmed and kept printable.
function giftNote(session) {
  var f = (session.custom_fields || []).filter(function (x) { return x.key === 'gift_note' && x.text && x.text.value; })[0];
  if (!f) return '';
  var note = String(f.text.value).replace(/[\r\n]+/g, ' ').trim().slice(0, 140);
  return note ? note + '  (3 | 4 | 5: i love you. i believe in you. i am proud of you.)' : '';
}

async function loadCatalog(env) {
  const origin = env.SITE_ORIGIN || 'https://ily345.com';
  const r = await fetch(origin + CATALOG_URL_PATH, { cf: { cacheTtl: 300, cacheEverything: true } });
  if (!r.ok) throw new Error('catalog unavailable');
  const products = await r.json();
  const byVariant = {};
  for (const p of products) for (const c of p.colors) for (const s of c.sizes) {
    byVariant[String(s.variant)] = {
      variant: s.variant, catalogVariant: s.catalogVariant, template: c.template, name: p.name, color: c.name, size: s.size === 'One size' ? '' : s.size,
      priceCents: Math.round(s.price * 100),
      image: 'https://cdn.printful.me/t/quick-stores/variants/' + c.images[0]
    };
  }
  return { byVariant };
}

async function stripe(env, method, path, form) {
  const r = await fetch(STRIPE + path, {
    method,
    headers: { Authorization: 'Bearer ' + env.STRIPE_SECRET_KEY, 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form ? form.toString() : undefined
  });
  const data = await r.json();
  if (!r.ok) throw new Error('stripe: ' + (data.error && data.error.message || r.status));
  return data;
}

async function printful(env, method, path, body) {
  const headers = { Authorization: 'Bearer ' + env.PRINTFUL_TOKEN, 'Content-Type': 'application/json' };
  if (env.PRINTFUL_STORE_ID) headers['X-PF-Store-Id'] = String(env.PRINTFUL_STORE_ID);
  const r = await fetch(PF + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error('printful ' + r.status + ': ' + (data.error && data.error.message || data.result || ''));
  return data;
}

async function verifyStripeSignature(payload, header, secret) {
  if (!secret) return false;
  const parts = Object.fromEntries(header.split(',').map(kv => kv.split('=')));
  const t = parts.t, v1 = parts.v1;
  if (!t || !v1) return false;
  if (Math.abs(Date.now() / 1000 - Number(t)) > 300) return false;
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const mac = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(t + '.' + payload));
  const hex = [...new Uint8Array(mac)].map(b => b.toString(16).padStart(2, '0')).join('');
  return timingSafeEqual(hex, v1);
}
function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let out = 0;
  for (let i = 0; i < a.length; i++) out |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return out === 0;
}
function cents(n) { return (Number(n || 0) / 100).toFixed(2); }
function json(obj, status, headers) { return new Response(JSON.stringify(obj), { status: status || 200, headers: { 'Content-Type': 'application/json', ...(headers || {}) } }); }
function corsHeaders(request, env) {
  const allowed = [env.SITE_ORIGIN || 'https://ily345.com', 'https://ily345.com', 'https://www.ily345.com', 'http://localhost:8345'];
  const origin = request.headers.get('Origin') || '';
  return {
    'Access-Control-Allow-Origin': allowed.includes(origin) ? origin : allowed[0],
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Vary': 'Origin'
  };
}
