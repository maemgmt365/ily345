// Registers the worker's /webhook URL with Stripe and prints the signing secret.
// Usage: STRIPE_SECRET_KEY=sk_... WORKER_URL=https://ily345-checkout.<you>.workers.dev node tools/setup-stripe-webhook.mjs
const key = process.env.STRIPE_SECRET_KEY, url = process.env.WORKER_URL;
if (!key || !url) { console.error('STRIPE_SECRET_KEY and WORKER_URL required'); process.exit(1); }
const form = new URLSearchParams();
form.set('url', url.replace(/\/$/, '') + '/webhook');
form.set('enabled_events[0]', 'checkout.session.completed');
form.set('description', 'ily345 checkout worker');
const r = await fetch('https://api.stripe.com/v1/webhook_endpoints', { method: 'POST', headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/x-www-form-urlencoded' }, body: form });
const j = await r.json();
if (!r.ok) { console.error(j); process.exit(1); }
console.log('webhook id', j.id);
console.log('STRIPE_WEBHOOK_SECRET=' + j.secret);
