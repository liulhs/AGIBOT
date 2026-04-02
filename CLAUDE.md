# AGIBOT X2 — Project Instructions

## Cloud Deployment

**NEVER deploy SAM stacks manually.** Always use `cloud/deploy.sh` which:
1. Sources `.env` and validates all secrets before deploy
2. Checks Stripe key format (`sk_test_*`/`sk_live_*`, `whsec_*`)
3. Verifies Lambda env vars post-deploy (catches `USE_PREVIOUS` bug)

If Lambdas already have broken secrets, run `cloud/fix-secrets.sh`.

See `.claude/skills/sam-deploy-with-secrets/SKILL.md` for full context on the NoEcho parameter bug.
