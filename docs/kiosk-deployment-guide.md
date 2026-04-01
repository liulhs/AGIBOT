# X2 Dance Kiosk — Robot Deployment Guide

How to deploy the Dance Kiosk service to a new X2 robot.

## Prerequisites

- SSH access to the robot (e.g. `ssh X2`)
- AWS CLI configured with IoT Core permissions
- The cloud stack already deployed (SAM template in `cloud/infra/template.yaml`)
- Robot running AGIBOT software (`agibot_software.service` active)

## 1. Choose a Robot ID

Pick a unique ID for the robot (e.g. `x2-002`). This ID is used across MQTT topics, DynamoDB, and the SPA.

## 2. Create AWS IoT Core Thing and Certificates

```bash
# Create the IoT Thing
aws iot create-thing --thing-name <ROBOT_ID>

# Create certificates
aws iot create-keys-and-certificate \
  --set-as-active \
  --certificate-pem-outfile cert.pem \
  --public-key-outfile public.key \
  --private-key-outfile private.key

# Save the certificate ARN from the output — you'll need it below

# Download the root CA
curl -o AmazonRootCA1.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem
```

## 3. Attach IoT Policy and Thing to Certificate

```bash
# Attach the policy (already created by the SAM stack)
aws iot attach-policy \
  --policy-name X2DanceKiosk-RobotPolicy \
  --target <CERTIFICATE_ARN>

# Attach the Thing
aws iot attach-thing-principal \
  --thing-name <ROBOT_ID> \
  --principal <CERTIFICATE_ARN>
```

## 4. Get the IoT Endpoint

```bash
aws iot describe-endpoint --endpoint-type iot:Data-ATS --query 'endpointAddress' --output text
# e.g. a1thbiemoccm90-ats.iot.us-east-2.amazonaws.com
```

## 5. Copy Files to Robot

```bash
# Copy the x2_api directory
scp -r x2_api/ X2:/home/run/x2_api/

# Copy certificates
ssh X2 "mkdir -p /home/run/x2_api/certs"
scp cert.pem private.key AmazonRootCA1.pem X2:/home/run/x2_api/certs/

# Make scripts executable
ssh X2 "chmod +x /home/run/x2_api/run.sh /home/run/x2_api/mqtt_run.sh"
```

Required cert files in `/home/run/x2_api/certs/`:
- `cert.pem` — device certificate
- `private.key` — private key
- `AmazonRootCA1.pem` — Amazon root CA

## 6. Install Python Dependencies

```bash
ssh X2 "pip3 install requests awsiotsdk"
```

The REST API uses only stdlib + Flask (already on the robot via ROS2). The MQTT client needs `requests` and `awsiotsdk`.

## 7. Install systemd Services

### REST API service

```bash
ssh X2 "sudo tee /etc/systemd/system/x2-motion-api.service > /dev/null << 'EOF'
[Unit]
Description=X2 Motion REST API
After=agibot_software.service
Wants=agibot_software.service

[Service]
Type=simple
User=run
WorkingDirectory=/home/run/x2_api
ExecStart=/home/run/x2_api/run.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"
```

### MQTT client service

Replace `<ROBOT_ID>` and `<IOT_ENDPOINT>` with the values from steps 1 and 4.

```bash
ssh X2 "sudo tee /etc/systemd/system/x2-mqtt-client.service > /dev/null << 'EOF'
[Unit]
Description=X2 MQTT Client (AWS IoT Core)
After=agibot_software.service x2-motion-api.service
Wants=agibot_software.service
Requires=x2-motion-api.service

[Service]
Type=simple
User=run
WorkingDirectory=/home/run/x2_api
ExecStart=/home/run/x2_api/mqtt_run.sh
Restart=on-failure
RestartSec=5
Environment=X2_ROBOT_ID=<ROBOT_ID>
Environment=X2_IOT_ENDPOINT=<IOT_ENDPOINT>
Environment=X2_CERT_PATH=/home/run/x2_api/certs

[Install]
WantedBy=multi-user.target
EOF"
```

### Enable and start

```bash
ssh X2 "sudo systemctl daemon-reload && \
  sudo systemctl enable x2-motion-api x2-mqtt-client && \
  sudo systemctl start x2-motion-api && \
  sleep 3 && \
  sudo systemctl start x2-mqtt-client"
```

The MQTT client must start after the REST API. The `Requires=` and `After=` directives handle this on boot, but for the first manual start, give the REST API a few seconds to initialize the ROS2 bridge.

## 8. Verify

```bash
# Both services should be active
ssh X2 "systemctl status x2-motion-api x2-mqtt-client --no-pager"

# REST API responds
ssh X2 "curl -s http://127.0.0.1:8080/api/v1/health"

# MQTT client connected and publishing heartbeats
ssh X2 "journalctl -u x2-mqtt-client --since '1 min ago' --no-pager"

# Robot shows up in the cloud
curl -s https://x37qk3dqwc.execute-api.us-east-2.amazonaws.com/prod/api/status/<ROBOT_ID>
```

## 9. Update the SPA (if needed)

The payment page at `cloud/spa/index.html` has a hardcoded `robot_id`. If deploying a second robot with its own kiosk, update the `robot_id` in the checkout metadata or add a robot selector to the SPA.

## Service Architecture

```
                  Internet
                     │
        Stripe webhook → Lambda (handle_webhook)
                     │
              AWS IoT Core (MQTT)
                     │
            ┌────────┴────────┐
            │   Robot (X2)    │
            │                 │
            │  mqtt_client.py │ ← x2-mqtt-client.service
            │       │ REST    │
            │  server.py      │ ← x2-motion-api.service
            │       │ ROS2    │
            │  AGIBOT SDK     │ ← agibot_software.service
            └─────────────────┘
```

## Troubleshooting

| Symptom | Check |
|---------|-------|
| MQTT client crashes with DNS error | Network not ready at boot — systemd will auto-restart it |
| `Connection refused` to REST API | `systemctl status x2-motion-api` — is it running? |
| Mode is `UNKNOWN` | REST API can't reach ROS2 — check `agibot_software.service` |
| Payment goes through but no motion | Check `journalctl -u x2-mqtt-client` for errors |
| Robot doesn't stand before dancing | Ensure `auto_stand: true` in webhook payload |
