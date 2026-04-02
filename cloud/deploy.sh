#!/bin/bash
# cloud/deploy.sh — SAM deploy with secret validation
# Prevents the USE_PREVIOUS placeholder bug on NoEcho parameters.
set -euo pipefail
cd "$(dirname "$0")/.."

# ── Pre-flight: source and validate secrets ──────────────────
echo "=== Pre-flight: validating secrets ==="

if [ ! -f .env ]; then
    echo "FATAL: .env file not found. Create it from .env.example" >&2
    exit 1
fi
source .env

REQUIRED_VARS=(STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET STRIPE_PRICE_CENTS DOMAIN_NAME IOT_ENDPOINT)
for var in "${REQUIRED_VARS[@]}"; do
    val="${!var}"
    if [ -z "$val" ] || [ "$val" = "USE_PREVIOUS" ]; then
        echo "FATAL: $var is empty or placeholder. Aborting." >&2
        exit 1
    fi
done

# Format checks
[[ "$STRIPE_SECRET_KEY" == sk_test_* ]] || [[ "$STRIPE_SECRET_KEY" == sk_live_* ]] || {
    echo "FATAL: STRIPE_SECRET_KEY doesn't look like a Stripe key: ${STRIPE_SECRET_KEY:0:15}..." >&2
    exit 1
}
[[ "$STRIPE_WEBHOOK_SECRET" == whsec_* ]] || {
    echo "FATAL: STRIPE_WEBHOOK_SECRET doesn't start with whsec_" >&2
    exit 1
}

echo "Pre-flight OK."
echo "  STRIPE_SECRET_KEY = ${STRIPE_SECRET_KEY:0:12}..."
echo "  STRIPE_WEBHOOK_SECRET = ${STRIPE_WEBHOOK_SECRET:0:10}..."
echo "  DOMAIN_NAME = $DOMAIN_NAME"
echo "  IOT_ENDPOINT = $IOT_ENDPOINT"
echo ""

# ── Build & Deploy ───────────────────────────────────────────
echo "=== Building SAM application ==="
cd cloud/infra
sam build

echo ""
echo "=== Deploying stack ==="
sam deploy --stack-name X2DanceKiosk --resolve-s3 --capabilities CAPABILITY_IAM \
    --no-confirm-changeset --parameter-overrides \
    "StripeSecretKey=$STRIPE_SECRET_KEY" \
    "StripeWebhookSecret=$STRIPE_WEBHOOK_SECRET" \
    "StripePriceCents=$STRIPE_PRICE_CENTS" \
    "DomainName=$DOMAIN_NAME" \
    "IoTEndpoint=$IOT_ENDPOINT"

# ── Post-flight: verify Lambda env vars ──────────────────────
echo ""
echo "=== Post-flight: verifying Lambda env vars ==="
LAMBDAS=(X2DanceKiosk-CreateCheckout X2DanceKiosk-HandleWebhook X2DanceKiosk-GetStatus X2DanceKiosk-SendCommand)
REGION=us-east-2
ALL_OK=true

for fn in "${LAMBDAS[@]}"; do
    env_json=$(aws lambda get-function-configuration \
        --function-name "$fn" --region "$REGION" \
        --query 'Environment.Variables' --output json 2>/dev/null || echo "{}")

    if echo "$env_json" | grep -q '"USE_PREVIOUS"'; then
        echo "FATAL: $fn has USE_PREVIOUS in env vars!" >&2
        echo "$env_json" | python3 -m json.tool >&2
        ALL_OK=false
        continue
    fi

    stripe_key=$(echo "$env_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('STRIPE_SECRET_KEY',''))" 2>/dev/null)
    if [ -n "$stripe_key" ] && [[ "$stripe_key" != sk_test_* ]] && [[ "$stripe_key" != sk_live_* ]]; then
        echo "FATAL: $fn STRIPE_SECRET_KEY is malformed: ${stripe_key:0:15}..." >&2
        ALL_OK=false
        continue
    fi

    echo "  $fn ✓"
done

if [ "$ALL_OK" = false ]; then
    echo ""
    echo "DEPLOY SUCCEEDED BUT LAMBDA ENV VARS ARE BROKEN." >&2
    echo "Run: source .env && cloud/fix-secrets.sh" >&2
    exit 1
fi

echo ""
echo "=== Deploy complete. All checks passed. ==="
