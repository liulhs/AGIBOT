---
name: sam-deploy-with-secrets
description: Use when deploying SAM/CloudFormation stacks that have NoEcho secret parameters (Stripe keys, API keys, webhook secrets), or when a Lambda returns authentication errors after a deploy. Prevents the USE_PREVIOUS placeholder bug.
---

# SAM Deploy with Secrets

## Overview

SAM `NoEcho` parameters silently accept empty or placeholder values. If you deploy without sourcing `.env` or with unset variables, Lambdas get broken secrets (literal `USE_PREVIOUS`, empty strings). This skill enforces a pre-flight check that catches this before deploy, and a post-flight verification after.

## When to Use

- Deploying any SAM/CloudFormation stack in this project
- Lambda throws `AuthenticationError: Invalid API Key`
- Stripe checkout returns "Failed to start checkout"
- Any Lambda env var contains `USE_PREVIOUS` or is empty

## The Problem

```
# What goes wrong:
sam deploy --parameter-overrides "StripeSecretKey=$STRIPE_SECRET_KEY"
#                                                 ^^^^^^^^^^^^^^^^
#                                    If unset → passes empty string
#                                    SAM accepts it silently
#                                    Lambda gets "" or "USE_PREVIOUS"
```

CloudFormation `NoEcho` parameters never echo back their stored value. On redeploy, if the parameter isn't explicitly provided, SAM may resolve it as the literal string `USE_PREVIOUS` instead of the actual secret.

## Deploy Checklist

### Pre-flight (BEFORE `sam deploy`)

```bash
# 1. Source secrets
source .env

# 2. Verify every NoEcho parameter is set and non-empty
REQUIRED_VARS=(STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET STRIPE_PRICE_CENTS DOMAIN_NAME IOT_ENDPOINT)
for var in "${REQUIRED_VARS[@]}"; do
  val="${!var}"
  if [ -z "$val" ] || [ "$val" = "USE_PREVIOUS" ]; then
    echo "FATAL: $var is empty or placeholder. Aborting." >&2
    exit 1
  fi
done

# 3. Sanity-check key format
[[ "$STRIPE_SECRET_KEY" == sk_test_* ]] || [[ "$STRIPE_SECRET_KEY" == sk_live_* ]] || {
  echo "FATAL: STRIPE_SECRET_KEY doesn't look like a Stripe key: ${STRIPE_SECRET_KEY:0:10}..." >&2
  exit 1
}
[[ "$STRIPE_WEBHOOK_SECRET" == whsec_* ]] || {
  echo "FATAL: STRIPE_WEBHOOK_SECRET doesn't look like a webhook secret" >&2
  exit 1
}

echo "Pre-flight OK. Deploying..."
```

### Deploy

```bash
cd cloud/infra
sam build
sam deploy --stack-name X2DanceKiosk --resolve-s3 --capabilities CAPABILITY_IAM \
  --no-confirm-changeset --parameter-overrides \
  "StripeSecretKey=$STRIPE_SECRET_KEY" \
  "StripeWebhookSecret=$STRIPE_WEBHOOK_SECRET" \
  "StripePriceCents=$STRIPE_PRICE_CENTS" \
  "DomainName=$DOMAIN_NAME" \
  "IoTEndpoint=$IOT_ENDPOINT"
```

### Post-flight (AFTER `sam deploy`)

```bash
# Verify Lambda env vars don't contain placeholders
LAMBDAS=(X2DanceKiosk-CreateCheckout X2DanceKiosk-HandleWebhook X2DanceKiosk-GetStatus X2DanceKiosk-SendCommand)
REGION=us-east-2

for fn in "${LAMBDAS[@]}"; do
  echo "Checking $fn..."
  env_json=$(aws lambda get-function-configuration \
    --function-name "$fn" --region "$REGION" \
    --query 'Environment.Variables' --output json 2>/dev/null)

  # Check for placeholder values
  if echo "$env_json" | grep -q '"USE_PREVIOUS"'; then
    echo "FATAL: $fn has USE_PREVIOUS in env vars!" >&2
    echo "$env_json" | python3 -m json.tool >&2
    exit 1
  fi

  # Check Stripe key format if present
  stripe_key=$(echo "$env_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('STRIPE_SECRET_KEY',''))" 2>/dev/null)
  if [ -n "$stripe_key" ] && [[ "$stripe_key" != sk_test_* ]] && [[ "$stripe_key" != sk_live_* ]]; then
    echo "FATAL: $fn STRIPE_SECRET_KEY is malformed: ${stripe_key:0:10}..." >&2
    exit 1
  fi
done

echo "Post-flight OK. All Lambdas verified."
```

## Quick Fix (when already broken)

If Lambdas already have bad keys, fix without a full redeploy:

```bash
source .env

aws lambda update-function-configuration \
  --function-name X2DanceKiosk-CreateCheckout \
  --region us-east-2 \
  --environment "$(aws lambda get-function-configuration \
    --function-name X2DanceKiosk-CreateCheckout \
    --region us-east-2 \
    --query 'Environment.Variables' --output json | \
    python3 -c "
import sys, json
v = json.load(sys.stdin)
v['STRIPE_SECRET_KEY'] = '$STRIPE_SECRET_KEY'
print(json.dumps({'Variables': v}))
")"
```

Repeat for each affected Lambda, adding `STRIPE_WEBHOOK_SECRET` where applicable.

## Common Mistakes

| Mistake | Result | Fix |
|---------|--------|-----|
| Forget `source .env` | Empty params passed to SAM | Pre-flight check catches this |
| Redeploy with `--resolve-parameters` | SAM uses `UsePreviousValue` for NoEcho | Always pass secrets explicitly |
| Assume SAM validates secrets | It doesn't — any string is accepted | Post-flight verification |
| Fix one Lambda, forget others | Partial fix, webhook still broken | Loop over all Lambdas |

## Files

| File | Role |
|------|------|
| `.env` | Secret values (gitignored) |
| `cloud/infra/template.yaml` | SAM template with `NoEcho` params |
| `cloud/lambdas/create_checkout.py` | Uses `STRIPE_SECRET_KEY` |
| `cloud/lambdas/handle_webhook.py` | Uses `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` |
