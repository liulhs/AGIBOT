# cloud/lambdas/send_command.py
"""Lambda: Send a command directly to the robot via MQTT (no payment required)."""
import json
import os
import uuid
from datetime import datetime, timezone

import boto3

IOT_ENDPOINT = os.environ["IOT_ENDPOINT"]
STATE_TABLE = os.environ["ROBOT_STATE_TABLE"]

dynamodb = boto3.resource("dynamodb")
state_table = dynamodb.Table(STATE_TABLE)
iot_client = boto3.client("iot-data", endpoint_url=f"https://{IOT_ENDPOINT}")


def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    robot_id = body.get("robot_id", "")
    action = body.get("action", "")
    motion_id = body.get("motion_id")
    area = body.get("area", 11)

    if not robot_id or not action:
        return _response(400, {"error": "robot_id and action required"})

    if action != "play_preset":
        return _response(400, {"error": "Only play_preset action is supported"})

    if motion_id is None:
        return _response(400, {"error": "motion_id required"})

    # Check robot state — reject if busy
    result = state_table.get_item(Key={"robot_id": robot_id})
    item = result.get("Item", {})
    state = item.get("state", "unknown")

    if state == "dancing":
        return _response(409, {"error": "Robot is busy", "state": "dancing"})

    # Publish MQTT command
    now = datetime.now(timezone.utc).isoformat()
    command = {
        "request_id": str(uuid.uuid4()),
        "action": "play_preset",
        "payload": {
            "motion_id": int(motion_id),
            "area": int(area),
        },
        "timestamp": now,
    }

    topic = f"x2/{robot_id}/command/preset/play"
    iot_client.publish(
        topic=topic,
        qos=1,
        payload=json.dumps(command).encode("utf-8"),
    )

    return _response(200, {
        "status": "command_sent",
        "robot_id": robot_id,
        "action": action,
        "motion_id": motion_id,
    })


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
