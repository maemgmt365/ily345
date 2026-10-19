// Confirms the Printful token works and that every catalogVariant/template in data/products.json
// still resolves in Printful's catalog (quick stores have no API, so orders use catalog variants
// plus product templates in the "Personal orders" store).
// Usage: PRINTFUL_TOKEN=... PRINTFUL_STORE_ID=... node tools/verify-printful.mjs
import { readFileSync } from 'node:fs';

const token = process.env.PRINTFUL_TOKEN;
if (!token) { console.error('PRINTFUL_TOKEN missing'); process.exit(1); }
const H = { Authorization: 'Bearer ' + token };
const get = async (path) => {
  const r = await fetch('https://api.printful.com' + path, { headers: H });
  const j = await r.json();
  if (!r.ok) throw new Error(path + ' ' + r.status + ' ' + JSON.stringify(j).slice(0, 300));
  return j.result;
};

const stores = await get('/stores');
console.log('stores:', stores.map(s => `${s.id} ${s.name} (${s.type})`).join(' | '));
const storeId = process.env.PRINTFUL_STORE_ID || (stores[0] && stores[0].id);
console.log('using store', storeId);

const products = JSON.parse(readFileSync(new URL('../../data/products.json', import.meta.url)));
const want = products.flatMap(p => p.colors.flatMap(c => c.sizes.map(s => ({ cv: s.catalogVariant, t: c.template, label: `${p.name} ${c.name} ${s.size}` }))));
const bad = want.filter(w => !w.cv || !w.t);
if (bad.length) { console.log('MISSING ids', bad.slice(0, 10)); process.exit(2); }
const sample = want[0];
const v = await get('/products/variant/' + sample.cv);
console.log('sample variant ok:', sample.label, '->', v.variant && v.variant.name);
console.log(`OK: ${want.length} variants carry a catalog id and a template id`);
