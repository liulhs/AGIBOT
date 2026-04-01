# cloud/lambdas/handle_webhook.py
"""Lambda: Handle Stripe webhook → verify payment → send MQTT command to robot."""
import json
import os
from datetime import datetime, timezone

import stripe
import boto3

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
WEBHOOK_SECRET = os.environ["STRIPE_WEBHOOK_SECRET"]
IOT_ENDPOINT = os.environ["IOT_ENDPOINT"]
STATE_TABLE = os.environ["ROBOT_STATE_TABLE"]
TX_TABLE = os.environ["TRANSACTIONS_TABLE"]

dynamodb = boto3.resource("dynamodb")
state_table = dynamodb.Table(STATE_TABLE)
tx_table = dynamodb.Table(TX_TABLE)
iot_client = boto3.client("iot-data", endpoint_url=f"https://{IOT_ENDPOINT}")


def lambda_handler(event, context):
    body = event.get("body", "")
    sig_header = event.get("headers", {}).get("stripe-signature", "")

    # Verify webhook signature
    try:
        evt = stripe.Webhook.construct_event(body, sig_header, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        return _response(400, {"error": "Invalid signature"})
    except Exception as e:
        return _response(400, {"error": str(e)})

    if evt["type"] != "checkout.session.completed":
        return _response(200, {"status": "ignored", "type": evt["type"]})

    session = evt["data"]["object"]
    metadata = session.get("metadata", {})
    robot_id = metadata.get("robot_id", "")
    motion_id = metadata.get("motion_id", "")
    amount = session.get("amount_total", 0)
    session_id = session["id"]

    if not robot_id or not motion_id:
        return _response(400, {"error": "Missing metadata"})

    # Check robot state — refund if busy
    result = state_table.get_item(Key={"robot_id": robot_id})
    item = result.get("Item", {})
    state = item.get("state", "unknown")

    if state == "dancing":
        stripe.Refund.create(payment_intent=session["payment_intent"])
        _log_transaction(session_id, robot_id, motion_id, amount, "refunded")
        return _response(200, {"status": "refunded", "reason": "robot_busy"})

    # Update robot state to dancing
    now = datetime.now(timezone.utc).isoformat()
    state_table.put_item(Item={
        "robot_id": robot_id,
        "state": "dancing",
        "current_motion": motion_id,
        "last_updated": now,
    })

    # Publish MQTT command
    command = {
        "request_id": session_id,
        "action": "play_motion",
        "payload": {
            "motion_id": motion_id,
            "interrupt": False,
            "auto_stand": True,
        },
        "timestamp": now,
    }

    topic = f"x2/{robot_id}/command/motion/play"
    iot_client.publish(
        topic=topic,
        qos=1,
        payload=json.dumps(command).encode("utf-8"),
    )

    _log_transaction(session_id, robot_id, motion_id, amount, "completed")

    return _response(200, {"status": "command_sent", "robot_id": robot_id, "motion_id": motion_id})


def _log_transaction(session_id, robot_id, motion_id, amount, status):
    tx_table.put_item(Item={
        "transaction_id": session_id,
        "robot_id": robot_id,
        "motion_id": motion_id,
        "amount_cents": amount,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
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
