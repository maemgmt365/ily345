#!/usr/bin/env bash
# One-shot deploy for the ily345 checkout worker. Run from the repo root on a machine with
# internet and a Cloudflare login. Needs: STRIPE_SECRET_KEY, PRINTFUL_TOKEN in the environment.
set -euo pipefail
cd "$(dirname "$0")"
: "${STRIPE_SECRET_KEY:?set STRIPE_SECRET_KEY}"; : "${PRINTFUL_TOKEN:?set PRINTFUL_TOKEN}"

echo "== 1. printful: token + store + variant check"
PRINTFUL_TOKEN="$PRINTFUL_TOKEN" node tools/verify-printful.mjs | tee /tmp/pf-verify.txt
STORE_ID=$(grep -o 'using store [0-9]*' /tmp/pf-verify.txt | awk '{print $3}')
sed -i.bak "s/^PRINTFUL_STORE_ID = .*/PRINTFUL_STORE_ID = \"$STORE_ID\"/" wrangler.toml && rm -f wrangler.toml.bak
echo "store id $STORE_ID written to wrangler.toml"

echo "== 2. cloudflare: install wrangler, login if needed, deploy"
npm install --silent
npx wrangler whoami >/dev/null 2>&1 || npx wrangler login </dev/tty >/dev/tty 2>&1
printf '%s' "$STRIPE_SECRET_KEY" | npx wrangler secret put STRIPE_SECRET_KEY
printf '%s' "$PRINTFUL_TOKEN"    | npx wrangler secret put PRINTFUL_TOKEN
DEPLOY_OUT=$(npx wrangler deploy 2>&1 | tee /dev/stderr)
WORKER_URL=$(echo "$DEPLOY_OUT" | grep -o 'https://[a-z0-9.-]*workers.dev' | head -1)
echo "worker url: $WORKER_URL"

echo "== 3. stripe: register webhook, store its secret"
STRIPE_SECRET_KEY="$STRIPE_SECRET_KEY" WORKER_URL="$WORKER_URL" node tools/setup-stripe-webhook.mjs | tee /tmp/wh.txt
WH=$(grep -o 'whsec_[A-Za-z0-9]*' /tmp/wh.txt)
printf '%s' "$WH" | npx wrangler secret put STRIPE_WEBHOOK_SECRET

echo "== 4. point the site at the worker"
sed -i.bak "s#https://ily345-checkout.REPLACE-ME.workers.dev#$WORKER_URL#" ../assets/site.js && rm -f ../assets/site.js.bak
grep -n "checkoutUrl" ../assets/site.js

echo "== 5. smoke test"
curl -s "$WORKER_URL/health"; echo
curl -s -X POST "$WORKER_URL/checkout" -H 'Content-Type: application/json' -H 'Origin: https://ily345.com' \
  -d '{"items":[{"variant":10765136,"qty":1}]}'; echo
echo "DONE. Commit and push the repo so assets/site.js carries the worker url."
