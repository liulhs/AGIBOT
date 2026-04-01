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
