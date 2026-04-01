# X2 LinkCraft Motion REST API

REST API running on the AgiBot X2 robot (Jetson Orin NX) that exposes LinkCraft motion control over HTTP. Bridges HTTP requests to ROS2 service calls, enabling cloud/web/mobile clients to trigger motions, query robot status, and manage state.

## Architecture

```
Client (cloud/web/mobile)
    │  HTTP :8080
    ▼
Flask App (server.py)
    │
    ├── auth.py            → API key validation
    ├── motion_catalog.py  → YAML → friendly motion IDs
    └── ros2_bridge.py     → rclpy service calls with retry
         │
         ▼  ROS2 Services
    MC (Motion Control on PC1)
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/health` | No | Health check |
| GET | `/api/v1/robot/state` | Yes | Current robot mode and status |
| POST | `/api/v1/robot/mode` | Yes | Switch robot mode |
| GET | `/api/v1/motions` | Yes | List all LinkCraft motions |
| GET | `/api/v1/motions/<id>` | Yes | Motion detail |
| POST | `/api/v1/motions/play` | Yes | Play a LinkCraft motion |
| POST | `/api/v1/motions/stop` | Yes | Stop current motion |
| POST | `/api/v1/presets/play` | Yes | Play a preset gesture |

## Quick Start

### Deploy to robot

```bash
scp -r x2_api/* X2:/home/run/x2_api/
ssh X2 "chmod +x /home/run/x2_api/run.sh"
```

### Run manually

```bash
ssh X2 "cd /home/run/x2_api && bash run.sh"
```

### Run as systemd service

```bash
ssh X2 "sudo cp /home/run/x2_api/x2-motion-api.service /etc/systemd/system/ && \
  sudo systemctl daemon-reload && \
  sudo systemctl enable x2-motion-api && \
  sudo systemctl start x2-motion-api"
```

## Usage Examples

```bash
# Health check
curl http://192.168.50.227:8080/api/v1/health

# List motions
curl -H "X-API-Key: x2-dev-key-change-me" http://192.168.50.227:8080/api/v1/motions

# Get robot state
curl -H "X-API-Key: x2-dev-key-change-me" http://192.168.50.227:8080/api/v1/robot/state

# Stand up
curl -X POST -H "X-API-Key: x2-dev-key-change-me" -H "Content-Type: application/json" \
  http://192.168.50.227:8080/api/v1/robot/mode -d '{"mode": "STAND_DEFAULT"}'

# Play golf swing (robot must be standing)
curl -X POST -H "X-API-Key: x2-dev-key-change-me" -H "Content-Type: application/json" \
  http://192.168.50.227:8080/api/v1/motions/play -d '{"motion_id": "golf_swing_pro"}'

# Play with auto-stand
curl -X POST -H "X-API-Key: x2-dev-key-change-me" -H "Content-Type: application/json" \
  http://192.168.50.227:8080/api/v1/motions/play -d '{"motion_id": "golf_swing_pro", "auto_stand": true}'

# Play preset wave gesture
curl -X POST -H "X-API-Key: x2-dev-key-change-me" -H "Content-Type: application/json" \
  http://192.168.50.227:8080/api/v1/presets/play -d '{"motion_id": 1002, "area": 2}'
```

## Testing

### Unit tests (run locally — needs `pyyaml` and `flask`)

```bash
cd x2_api && python3 -m pytest tests/test_motion_catalog.py tests/test_auth.py -v
```

### Integration tests (run against live API)

```bash
bash x2_api/tests/test_integration.sh http://192.168.50.227:8080
```

## Tech Stack

- Python 3.10, Flask 3.1.2, rclpy (ROS2 Humble)
- Runs on PC2 (Jetson Orin NX, 192.168.50.227)
- Bridges to MC on PC1 via ROS2 service calls

---

# X2 MQTT Client (AWS IoT Core)

MQTT client running on the X2 robot that connects to AWS IoT Core, receives dance commands from the cloud, and controls the robot via the same ROS2 bridge. Works alongside the REST API.

## Architecture

```
AWS IoT Core
    │  MQTT (TLS, X.509 mutual auth)
    ▼
mqtt_client.py (MqttCommandHandler)
    │
    ├── config.py            → MQTT topics, robot ID, cert paths
    ├── motion_catalog.py    → YAML → friendly motion IDs
    └── ros2_bridge.py       → rclpy service calls with retry
         │
         ▼  ROS2 Services
    MC (Motion Control on PC1)
```

## MQTT Topics

| Topic | Direction | Description |
|-------|-----------|-------------|
| `x2/{robot_id}/command/#` | Cloud → Robot | Incoming commands (play, stop, mode) |
| `x2/{robot_id}/status` | Robot → Cloud | State updates (idle/dancing/offline) |
| `x2/{robot_id}/status/heartbeat` | Robot → Cloud | Heartbeat every 30s |

## Command Format

Commands are JSON published to `x2/{robot_id}/command/...`:

```json
{
  "action": "play_motion",
  "request_id": "uuid",
  "payload": {
    "motion_id": "golf_swing_pro",
    "interrupt": false,
    "auto_stand": true
  }
}
```

Supported actions: `play_motion`, `stop_motion`, `set_mode`, `play_preset`

## Features

- **Last Will and Testament (LWT):** Auto-publishes `state: "offline"` if connection drops
- **Auto-registration:** Registers all LinkCraft motions at startup
- **Auto-stand:** Can automatically stand the robot before playing a motion
- **Heartbeat:** Publishes state every 30 seconds

## Certificates

Stored at `/home/run/x2_api/certs/` on the robot:

```
certs/
├── cert.pem           ← Device certificate
├── private.key        ← Private key
└── AmazonRootCA1.pem  ← Amazon root CA
```

Provisioned via `cloud/scripts/provision_robot.py`:

```bash
python cloud/scripts/provision_robot.py x2-001 --scp
```

## Deploy to Robot

```bash
# Copy files
scp x2_api/mqtt_client.py x2_api/mqtt_run.sh x2_api/config.py X2:/home/run/x2_api/
ssh X2 "chmod +x /home/run/x2_api/mqtt_run.sh"
```

## Run Manually

```bash
ssh X2
export X2_IOT_ENDPOINT=a1thbiemoccm90-ats.iot.us-east-2.amazonaws.com
cd /home/run/x2_api && bash mqtt_run.sh
```

## Systemd Service

The MQTT client runs as `x2-mqtt-client.service` — enabled and auto-starts on boot.

```bash
# Install (already done)
sudo cp /home/run/x2_api/x2-mqtt-client.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable x2-mqtt-client.service
sudo systemctl start x2-mqtt-client.service

# Management
sudo systemctl status x2-mqtt-client     # Check status
sudo systemctl restart x2-mqtt-client    # Restart
journalctl -u x2-mqtt-client -f          # Live logs
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `X2_ROBOT_ID` | `x2-001` | Robot identifier |
| `X2_IOT_ENDPOINT` | (none, required) | AWS IoT Core endpoint |
| `X2_CERT_PATH` | `/home/run/x2_api/certs` | Path to TLS certificates |

## Testing

```bash
cd x2_api && python3 -m pytest tests/test_mqtt_client.py -v
```

---

# Files on Robot (`/home/run/x2_api/`)

| File | Purpose |
|------|---------|
| `server.py` | Flask REST API (port 8080) |
| `mqtt_client.py` | MQTT client for AWS IoT Core |
| `ros2_bridge.py` | ROS2 service call wrapper with retry |
| `motion_catalog.py` | YAML-based motion catalog |
| `config.py` | Shared configuration (REST + MQTT) |
| `auth.py` | API key validation for REST |
| `run.sh` | REST API launcher |
| `mqtt_run.sh` | MQTT client launcher |
| `x2-motion-api.service` | systemd unit for REST API |
| `x2-mqtt-client.service` | systemd unit for MQTT client |
| `certs/` | AWS IoT X.509 certificates |

## Systemd Services on Robot

| Service | Status | Description |
|---------|--------|-------------|
| `x2-motion-api.service` | enabled, active | Flask REST API on port 8080 |
| `x2-mqtt-client.service` | enabled, active | AWS IoT Core MQTT client |

Both services are set to `Restart=on-failure` and start after `agibot_software.service`.

---

# AWS Cloud Stack (Dance Kiosk)

The cloud infrastructure supports a pay-per-dance kiosk web app.

## Architecture

```
Browser (CloudFront SPA)
    │
    ├── GET  /api/status/{robot_id}     → Lambda → DynamoDB
    ├── POST /api/checkout              → Lambda → Stripe Checkout
    └── POST /api/webhook/stripe        → Lambda → verify sig → MQTT publish
                                                       │
                                                       ▼
                                              AWS IoT Core
                                                       │
                                                       ▼
                                              Robot MQTT Client
```

## AWS Resources (CloudFormation stack: `X2DanceKiosk`)

| Resource | Type | Purpose |
|----------|------|---------|
| `X2DanceKiosk-RobotState` | DynamoDB | Robot state (updated by IoT Rule) |
| `X2DanceKiosk-Transactions` | DynamoDB | Payment transaction log |
| `X2DanceKiosk-CreateCheckout` | Lambda | Create Stripe Checkout Session |
| `X2DanceKiosk-HandleWebhook` | Lambda | Verify Stripe webhook, publish MQTT command |
| `X2DanceKiosk-GetStatus` | Lambda | Read robot state from DynamoDB |
| `X2DanceKioskStatusToDynamo` | IoT Rule | `SELECT * FROM 'x2/+/status'` → DynamoDB PutItem |
| `x2-dance-kiosk-web-*` | S3 | Static web assets |
| CloudFront | CDN | HTTPS frontend |
| HttpApi | API Gateway | REST API endpoints |

## URLs

| Service | URL |
|---------|-----|
| Web kiosk | `https://d3h2rdy9lq3b29.cloudfront.net` |
| API Gateway | `https://x37qk3dqwc.execute-api.us-east-2.amazonaws.com/prod` |
| IoT Endpoint | `a1thbiemoccm90-ats.iot.us-east-2.amazonaws.com` |

## IoT Thing

| Property | Value |
|----------|-------|
| Thing Name | `x2-001` |
| Policy | `X2DanceKiosk-x2-001` |
| Allowed actions | Connect, Subscribe (`command/*`), Receive (`command/*`), Publish (`status`, `status/*`) |

## Stripe Integration

- **Checkout Sessions** created by Lambda with `robot_id` + `motion_id` metadata
- **Webhook** at `/api/webhook/stripe` listens for `checkout.session.completed`
- On successful payment: publishes MQTT command to `x2/{robot_id}/command/motion/play`
- If robot busy: issues automatic refund

## Deploy Cloud Stack

```bash
source .env
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

## Upload Web Assets

```bash
aws s3 sync cloud/web/ s3://x2-dance-kiosk-web-202716106225/ --delete
aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"
```

## Provision a New Robot

```bash
python cloud/scripts/provision_robot.py x2-002 --scp
```
