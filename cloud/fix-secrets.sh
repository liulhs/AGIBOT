#!/bin/bash
# cloud/fix-secrets.sh — Hot-fix Lambda env vars when USE_PREVIOUS leaked through
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "FATAL: .env file not found." >&2
    exit 1
fi
source .env

REGION=us-east-2
LAMBDAS_WITH_STRIPE_KEY=(X2DanceKiosk-CreateCheckout X2DanceKiosk-HandleWebhook)
LAMBDAS_WITH_WEBHOOK=(X2DanceKiosk-HandleWebhook)

echo "=== Fixing Lambda secrets ==="

for fn in "${LAMBDAS_WITH_STRIPE_KEY[@]}"; do
    echo "Updating $fn..."
    current=$(aws lambda get-function-configuration \
        --function-name "$fn" --region "$REGION" \
        --query 'Environment.Variables' --output json)

    updated=$(echo "$current" | python3 -c "
import sys, json, os
v = json.load(sys.stdin)
v['STRIPE_SECRET_KEY'] = os.environ['STRIPE_SECRET_KEY']
if '$fn' in ['X2DanceKiosk-HandleWebhook']:
    v['STRIPE_WEBHOOK_SECRET'] = os.environ['STRIPE_WEBHOOK_SECRET']
print(json.dumps({'Variables': v}))
")

    aws lambda update-function-configuration \
        --function-name "$fn" --region "$REGION" \
        --environment "$updated" \
        --query 'FunctionName' --output text
    echo "  $fn ✓"
done

echo ""
echo "=== Verifying ==="
for fn in "${LAMBDAS_WITH_STRIPE_KEY[@]}"; do
    key=$(aws lambda get-function-configuration \
        --function-name "$fn" --region "$REGION" \
        --query 'Environment.Variables.STRIPE_SECRET_KEY' --output text)
    if [[ "$key" == sk_test_* ]] || [[ "$key" == sk_live_* ]]; then
        echo "  $fn: ${key:0:12}... ✓"
    else
        echo "  $fn: STILL BROKEN — $key" >&2
    fi
done

echo ""
echo "Done. Stripe checkout should work now."
