# cloud/lambdas/create_checkout.py
"""Lambda: Create a Stripe Checkout session for a dance payment."""
import json
import os
import stripe
import boto3

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
PRICE_CENTS = int(os.environ.get("STRIPE_PRICE_CENTS", "200"))
DOMAIN = os.environ.get("DOMAIN_NAME", "localhost")
TABLE = os.environ["ROBOT_STATE_TABLE"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE)


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON"})

    robot_id = body.get("robot_id", "")
    motion_id = body.get("motion_id", "")

    if not robot_id or not motion_id:
        return _response(400, {"error": "robot_id and motion_id required"})

    # Check robot state
    result = table.get_item(Key={"robot_id": robot_id})
    item = result.get("Item")
    if item:
        state = item.get("state", "offline")
        if state == "dancing":
            return _response(409, {"error": "Robot is busy dancing", "state": state})
        if state == "offline":
            return _response(409, {"error": "Robot is offline", "state": state})

    # Create Stripe Checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"Robot Dance: {motion_id}"},
                "unit_amount": PRICE_CENTS,
            },
            "quantity": 1,
        }],
        mode="payment",
        metadata={"robot_id": robot_id, "motion_id": motion_id},
        success_url=f"https://{DOMAIN}/{robot_id}?success=true",
        cancel_url=f"https://{DOMAIN}/{robot_id}?cancelled=true",
    )

    return _response(200, {"checkout_url": session.url})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
