# cloud/lambdas/get_status.py
"""Lambda: Return current robot state from DynamoDB."""
import json
import os
import boto3

TABLE = os.environ["ROBOT_STATE_TABLE"]
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE)


def lambda_handler(event, context):
    robot_id = event.get("pathParameters", {}).get("robot_id", "")

    if not robot_id:
        return _response(400, {"error": "robot_id required"})

    result = table.get_item(Key={"robot_id": robot_id})
    item = result.get("Item")

    if not item:
        return _response(200, {
            "robot_id": robot_id,
            "state": "unknown",
            "current_motion": None,
            "last_updated": None,
        })

    return _response(200, {
        "robot_id": item.get("robot_id"),
        "state": item.get("state", "unknown"),
        "current_motion": item.get("current_motion"),
        "last_updated": item.get("last_updated"),
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
