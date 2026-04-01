#!/bin/bash
# x2_api/tests/test_integration.sh
# Run against a live X2 API server.
# Usage: bash test_integration.sh [host] [api_key]

HOST="${1:-http://192.168.50.227:8080}"
KEY="${2:-x2-dev-key-change-me}"
PASS=0
FAIL=0

check() {
    local desc="$1" expected_code="$2" method="$3" path="$4" body="$5"
    local args=(-s -o /tmp/x2_resp -w "%{http_code}" -X "$method" "${HOST}${path}" -H "X-API-Key: ${KEY}" -H "Content-Type: application/json")
    [ -n "$body" ] && args+=(-d "$body")
    code=$(curl "${args[@]}")
    if [ "$code" = "$expected_code" ]; then
        echo "PASS: $desc (HTTP $code)"
        ((PASS++))
    else
        echo "FAIL: $desc (expected $expected_code, got $code)"
        cat /tmp/x2_resp
        echo
        ((FAIL++))
    fi
}

echo "=== X2 Motion API Integration Tests ==="
echo "Target: $HOST"
echo

# Health (no auth)
check "Health check" 200 GET "/api/v1/health"

# Auth
check "No API key → 401" 401 GET "/api/v1/motions"
ORIG_KEY="$KEY"; KEY="wrong"
check "Wrong API key → 403" 403 GET "/api/v1/motions"
KEY="$ORIG_KEY"

# Robot state
check "Get robot state" 200 GET "/api/v1/robot/state"

# Motion list
check "List motions" 200 GET "/api/v1/motions"

# Motion detail
check "Get motion detail" 200 GET "/api/v1/motions/golf_swing_pro"
check "Unknown motion → 404" 404 GET "/api/v1/motions/nonexistent"

# Invalid mode
check "Invalid mode → 400" 400 POST "/api/v1/robot/mode" '{"mode": "INVALID"}'

echo
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
