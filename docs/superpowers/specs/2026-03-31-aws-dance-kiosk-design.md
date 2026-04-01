# X2 Dance Kiosk — AWS Cloud Architecture Design

> **Summary:** A pay-to-dance kiosk system where people scan a QR code near the robot, pick a dance on a mobile web page, pay via Stripe, and the robot performs the dance. Cloud infrastructure on AWS connects the payment flow to the robot over MQTT.

---

## 1. End-to-End Flow

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌───────────┐
│  QR Code    │────▶│  Mobile Web Page  │────▶│  Stripe Checkout │────▶│  Webhook  │
│  (on robot) │     │  (CloudFront/S3)  │     │  (hosted by      │     │  confirms │
│             │     │  Pick a dance     │     │   Stripe)        │     │  payment  │
└─────────────┘     └──────────────────┘     └──────────────────┘     └─────┬─────┘
                                                                            │
                                                                            ▼
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌───────────┐
│  Robot      │◀────│  AWS IoT Core    │◀────│  Lambda          │◀────│  API GW   │
│  dances!    │MQTT │  (topic:         │     │  (verify payment │     │  (Stripe  │
│             │     │   x2/{id}/cmd/)  │     │   → publish cmd) │     │  webhook) │
└──────┬──────┘     └──────────────────┘     └──────────────────┘     └───────────┘
       │ MQTT status
       ▼
  IoT Core → status topic → web page polls or receives "busy/idle"
```

### Step-by-step:

1. **Scan:** User scans QR code on/near the robot → opens `https://dance.yourdomain.com/{robot_id}`
2. **Browse:** Mobile web page shows available dances with names/thumbnails, robot's current status (idle/busy)
3. **Pay:** User taps a dance → redirected to Stripe Checkout (hosted payment page, PCI-compliant)
4. **Confirm:** Stripe sends a `checkout.session.completed` webhook to API Gateway → Lambda
5. **Command:** Lambda verifies the webhook signature, extracts `robot_id` and `motion_id`, publishes to IoT Core topic `x2/{robot_id}/command/motion/play`
6. **Execute:** Robot's MQTT client receives the message, calls `ros2_bridge.play_motion()`, publishes status to `x2/{robot_id}/status`
7. **Feedback:** Web page shows "Robot is dancing!" (polls status endpoint or uses WebSocket via IoT Core)

---

## 2. AWS Services

| Service | Role | Free Tier |
|---------|------|-----------|
| **S3 + CloudFront** | Host the static mobile web page | 1TB transfer/month |
| **API Gateway (HTTP)** | REST endpoints: `/api/checkout`, `/api/status/{robot_id}`, Stripe webhook receiver | 1M calls/month |
| **Lambda** | 3 functions: create-checkout, handle-webhook, get-status | 1M invocations/month |
| **IoT Core** | MQTT broker for robot connections, X.509 cert auth | 250K messages/month |
| **DynamoDB** | Store robot state (idle/busy/last_dance), transaction log | 25GB + 25 WCU/RCU |
| **Route 53** | DNS for custom domain | $0.50/zone/month |
| **ACM** | TLS certificate for custom domain | Free |

**Estimated cost at low volume (< 1000 dances/month):** Under $5/month (mostly Route 53). All other services fall within free tier.

---

## 3. Robot-Side MQTT Client

A new `mqtt_client.py` module runs alongside the existing Flask REST API as a separate systemd service. Both share `ros2_bridge.py` and `motion_catalog.py`.

### Topic Structure

```
x2/{robot_id}/command/motion/play     ← Cloud → Robot (trigger a dance)
x2/{robot_id}/command/motion/stop     ← Cloud → Robot (stop current dance)
x2/{robot_id}/command/mode            ← Cloud → Robot (switch robot mode)
x2/{robot_id}/command/preset/play     ← Cloud → Robot (play preset gesture)
x2/{robot_id}/status                  → Robot → Cloud (current state)
x2/{robot_id}/status/heartbeat        → Robot → Cloud (periodic alive signal)
```

### Command Message Format

```json
{
  "request_id": "uuid-v4",
  "action": "play_motion",
  "payload": {
    "motion_id": "golf_swing_pro",
    "interrupt": false,
    "auto_stand": true
  },
  "timestamp": "2026-03-31T12:00:00Z"
}
```

### Status Message Format

```json
{
  "robot_id": "x2-001",
  "state": "dancing",
  "current_motion": "golf_swing_pro",
  "mode": "STAND_DEFAULT",
  "uptime_sec": 3600,
  "timestamp": "2026-03-31T12:00:05Z"
}
```

### Robot MQTT Client Behavior

- Connects to AWS IoT Core on startup using X.509 device certificate
- Subscribes to `x2/{robot_id}/command/#`
- On receiving a command:
  1. Validate message format
  2. Check robot state (if busy → publish rejection to status topic)
  3. Execute via `ros2_bridge` (same code the REST API uses)
  4. Publish result to `x2/{robot_id}/status`
- Publishes heartbeat every 30 seconds to `x2/{robot_id}/status/heartbeat`
- Uses IoT Core Last Will and Testament (LWT) to publish `{"state": "offline"}` if connection drops

### Coexistence with REST API

```
systemd services on robot:
├── x2-motion-api.service     (Flask REST API — LAN access, port 8080)
└── x2-mqtt-client.service    (MQTT client — cloud access via IoT Core)

Both import from:
├── ros2_bridge.py
├── motion_catalog.py
└── config.py
```

**Important:** Both services share the same `rclpy` node? No — each runs in its own process with its own rclpy node. ROS2 service calls are stateless, so this is safe.

---

## 4. AWS IoT Core Setup

### Per-Robot Provisioning

Each robot is an IoT "Thing" with:
- **Thing name:** `x2-{serial}` (e.g., `x2-001`)
- **X.509 certificate:** unique per robot, generated during provisioning
- **IoT Policy:** scoped to that robot's topic namespace only

### IoT Policy (per robot)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iot:Connect",
      "Resource": "arn:aws:iot:{region}:{account}:client/x2-{robot_id}"
    },
    {
      "Effect": "Allow",
      "Action": "iot:Subscribe",
      "Resource": "arn:aws:iot:{region}:{account}:topicfilter/x2/{robot_id}/command/*"
    },
    {
      "Effect": "Allow",
      "Action": "iot:Receive",
      "Resource": "arn:aws:iot:{region}:{account}:topic/x2/{robot_id}/command/*"
    },
    {
      "Effect": "Allow",
      "Action": "iot:Publish",
      "Resource": "arn:aws:iot:{region}:{account}:topic/x2/{robot_id}/status/*"
    }
  ]
}
```

### Provisioning Script

A CLI tool (`scripts/provision_robot.py`) using `boto3`:
1. Creates IoT Thing `x2-{robot_id}`
2. Creates and attaches X.509 certificate
3. Attaches IoT policy
4. Downloads cert bundle (cert.pem, private.key, AmazonRootCA1.pem)
5. SCPs the cert bundle to the robot at `/home/run/x2_api/certs/`

---

## 5. Cloud API (Lambda Functions)

### 5a. `create-checkout` Lambda

**Trigger:** `POST /api/checkout` via API Gateway

**Request:**
```json
{
  "robot_id": "x2-001",
  "motion_id": "golf_swing_pro"
}
```

**Behavior:**
1. Query DynamoDB for robot state — if busy or offline, return 409
2. Create a Stripe Checkout Session with:
   - Fixed price amount (configured per deployment)
   - `metadata`: `{ robot_id, motion_id }`
   - `success_url`: `https://dance.yourdomain.com/{robot_id}?success=true`
   - `cancel_url`: `https://dance.yourdomain.com/{robot_id}?cancelled=true`
3. Return `{ checkout_url }` → frontend redirects to Stripe

### 5b. `handle-webhook` Lambda

**Trigger:** `POST /api/webhook/stripe` via API Gateway

**Behavior:**
1. Verify Stripe webhook signature (reject if invalid)
2. Handle `checkout.session.completed` event:
   - Extract `robot_id` and `motion_id` from metadata
   - Check robot state in DynamoDB — if busy, refund via Stripe API and return
   - Update DynamoDB: set robot state to `"dancing"`, record transaction
   - Publish MQTT command to `x2/{robot_id}/command/motion/play`
3. Log transaction to DynamoDB (timestamp, amount, motion_id, robot_id, status)

### 5c. `get-status` Lambda

**Trigger:** `GET /api/status/{robot_id}` via API Gateway

**Behavior:**
1. Read robot state from DynamoDB
2. Return `{ robot_id, state, current_motion, last_updated }`
3. No auth required (public endpoint — only returns non-sensitive state)

---

## 6. DynamoDB Tables

### `RobotState` Table

| Key | Type | Description |
|-----|------|-------------|
| `robot_id` (PK) | String | e.g. `x2-001` |
| `state` | String | `idle`, `dancing`, `offline` |
| `current_motion` | String | motion_id currently playing, or null |
| `last_heartbeat` | String (ISO 8601) | last heartbeat timestamp |
| `last_updated` | String (ISO 8601) | last state change |

### `Transactions` Table

| Key | Type | Description |
|-----|------|-------------|
| `transaction_id` (PK) | String | Stripe checkout session ID |
| `robot_id` (GSI) | String | which robot |
| `motion_id` | String | which dance |
| `amount_cents` | Number | price charged |
| `status` | String | `completed`, `refunded` |
| `created_at` | String (ISO 8601) | timestamp |

---

## 7. Mobile Web Page (Static SPA)

Hosted on S3 + CloudFront. Minimal, mobile-optimized, single page.

### URL Scheme

- `https://dance.yourdomain.com/{robot_id}` — main page for a specific robot
- QR code on each robot encodes its own URL

### Page Behavior

1. On load: fetch `GET /api/status/{robot_id}` — show robot state
2. If robot is idle: show dance menu (cards with name + thumbnail for each motion)
3. If robot is busy/dancing: show "Robot is performing! Check back in a moment." with auto-refresh
4. If robot is offline: show "Robot is offline" message
5. On dance tap: call `POST /api/checkout` → redirect to Stripe Checkout
6. On return from Stripe (success): show "Payment received! Robot is dancing 🎉" with status polling
7. On return from Stripe (cancel): show "Payment cancelled" and return to menu

### Tech

- Vanilla HTML/CSS/JS or lightweight framework (Preact/Alpine.js)
- No build step preferred — keep it simple, loads fast on mobile
- Responsive, works on any phone browser

---

## 8. Security

| Layer | Mechanism |
|-------|-----------|
| **Robot ↔ IoT Core** | Mutual TLS with X.509 device certificates |
| **Web ↔ API Gateway** | HTTPS (ACM certificate on CloudFront + API GW) |
| **Stripe webhooks** | Signature verification (`stripe-signature` header) |
| **Payment** | Stripe Checkout (hosted page — we never handle card data, PCI-compliant) |
| **IoT policy** | Each robot scoped to its own topic namespace only |
| **Lambda → IoT Core** | IAM role with `iot:Publish` permission scoped to `x2/*/command/*` |
| **DynamoDB** | IAM role, no public access |
| **Status endpoint** | Public read-only (no sensitive data exposed) |

**No API keys in the cloud path.** Robot auth = X.509 certs. Cloud API auth = Stripe handles payment auth, status is public read-only.

---

## 9. Robot State Machine

```
                ┌──────────┐
     startup    │          │  heartbeat timeout
   ┌───────────▶│  IDLE    │◀──────────────────┐
   │            │          │                    │
   │            └────┬─────┘                    │
   │                 │ receive play command      │
   │                 ▼                          │
   │            ┌──────────┐                    │
   │            │          │  motion completes  │
   │            │ DANCING  │───────────────────▶│
   │            │          │                    │
   │            └────┬─────┘                    │
   │                 │ connection lost           │
   │                 ▼                          │
   │            ┌──────────┐                    │
   │            │          │  reconnect         │
   │            │ OFFLINE  │───────────────────▶│
   │            │          │  (LWT published    │
   │            └──────────┘   by IoT Core)     │
   │                                            │
   └────────────────────────────────────────────┘
```

The robot publishes state transitions to `x2/{robot_id}/status`. An IoT Rule updates DynamoDB on every status message so the Lambdas always have current state.

---

## 10. IoT Rule — Status to DynamoDB

An IoT Core Rule automatically writes robot status updates to DynamoDB so Lambdas always have current state without querying the robot directly.

**Rule SQL:**
```sql
SELECT * FROM 'x2/+/status'
```

**Action:** DynamoDB PutItem → `RobotState` table

This means:
- When robot publishes to `x2/{robot_id}/status`, the rule writes `state`, `current_motion`, `last_updated` to DynamoDB
- When robot disconnects (LWT), IoT Core publishes `{"state": "offline"}` → same rule writes it to DynamoDB
- Lambdas (`get-status`, `handle-webhook`) read from DynamoDB, never from the robot directly

---

## 11. File Structure (New + Existing)

```
AGIBOT/
├── x2_api/                          # EXISTING — robot-side code
│   ├── server.py                    # Flask REST API (unchanged)
│   ├── ros2_bridge.py               # ROS2 calls (shared, unchanged)
│   ├── motion_catalog.py            # Motion catalog (shared, unchanged)
│   ├── config.py                    # Config (add MQTT settings)
│   ├── auth.py                      # REST API auth (unchanged)
│   ├── run.sh                       # REST API launcher (unchanged)
│   ├── mqtt_client.py               # NEW — MQTT client for IoT Core
│   ├── mqtt_run.sh                  # NEW — MQTT client launcher
│   ├── x2-mqtt-client.service       # NEW — systemd unit
│   ├── certs/                       # NEW — X.509 certs (gitignored)
│   └── tests/
│       ├── test_motion_catalog.py
│       ├── test_auth.py
│       ├── test_mqtt_client.py      # NEW
│       └── test_integration.sh
│
├── cloud/                           # NEW — AWS cloud infrastructure
│   ├── lambdas/
│   │   ├── create_checkout.py       # Stripe checkout session
│   │   ├── handle_webhook.py        # Stripe webhook → MQTT command
│   │   └── get_status.py            # Robot status query
│   ├── web/
│   │   ├── index.html               # Mobile web page (SPA)
│   │   ├── style.css
│   │   └── app.js
│   ├── infra/
│   │   └── template.yaml            # SAM/CloudFormation template
│   └── scripts/
│       └── provision_robot.py       # IoT Thing + cert provisioning
│
├── docs/
│   └── superpowers/
│       ├── specs/
│       │   └── 2026-03-31-aws-dance-kiosk-design.md  # This doc
│       └── plans/
│           └── 2026-03-31-x2-motion-api.md           # Existing
└── .gitignore                       # Add: certs/, .env
```

---

## 12. Configuration

### Environment Variables

**Robot (mqtt_client.py):**
| Variable | Default | Description |
|----------|---------|-------------|
| `X2_ROBOT_ID` | `x2-001` | This robot's ID |
| `X2_IOT_ENDPOINT` | — | AWS IoT Core endpoint (from `aws iot describe-endpoint`) |
| `X2_CERT_PATH` | `/home/run/x2_api/certs` | Directory containing cert.pem, private.key, AmazonRootCA1.pem |

**Cloud (Lambda env vars via SAM template):**
| Variable | Description |
|----------|-------------|
| `STRIPE_SECRET_KEY` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `STRIPE_PRICE_CENTS` | Fixed price per dance (e.g. `200` = $2.00) |
| `IOT_ENDPOINT` | AWS IoT Core endpoint |
| `ROBOT_STATE_TABLE` | DynamoDB table name for robot state |
| `TRANSACTIONS_TABLE` | DynamoDB table name for transactions |

---

## 13. Out of Scope (For Now)

- **Analytics dashboard** — transaction reports, popular dances, revenue
- **Multi-currency pricing** — single currency for now
- **User accounts / login** — anonymous one-shot payments
- **Video streaming** — watching the robot dance remotely
- **WeChat/Alipay** — Stripe only for now
- **Dance queue** — one-at-a-time with busy rejection
- **Admin panel** — manage robots, pricing, etc. (use AWS Console + Stripe Dashboard)
