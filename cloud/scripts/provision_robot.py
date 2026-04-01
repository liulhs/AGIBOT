#!/usr/bin/env python3
# cloud/scripts/provision_robot.py
"""Provision an X2 robot as an AWS IoT Thing with certs and policy.

Usage:
    python provision_robot.py <robot_id> [--scp]

Example:
    python provision_robot.py x2-001 --scp
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

import boto3

iot = boto3.client("iot")


def get_account_and_region():
    sts = boto3.client("sts")
    account = sts.get_caller_identity()["Account"]
    region = boto3.session.Session().region_name
    return account, region


def create_policy(robot_id: str, account: str, region: str) -> str:
    policy_name = f"X2DanceKiosk-{robot_id}"
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "iot:Connect",
                "Resource": f"arn:aws:iot:{region}:{account}:client/{robot_id}",
            },
            {
                "Effect": "Allow",
                "Action": "iot:Subscribe",
                "Resource": f"arn:aws:iot:{region}:{account}:topicfilter/x2/{robot_id}/command/*",
            },
            {
                "Effect": "Allow",
                "Action": "iot:Receive",
                "Resource": f"arn:aws:iot:{region}:{account}:topic/x2/{robot_id}/command/*",
            },
            {
                "Effect": "Allow",
                "Action": "iot:Publish",
                "Resource": [
                    f"arn:aws:iot:{region}:{account}:topic/x2/{robot_id}/status",
                    f"arn:aws:iot:{region}:{account}:topic/x2/{robot_id}/status/*",
                ],
            },
        ],
    }

    try:
        iot.create_policy(
            policyName=policy_name,
            policyDocument=json.dumps(policy_doc),
        )
        print(f"Created IoT policy: {policy_name}")
    except iot.exceptions.ResourceAlreadyExistsException:
        print(f"IoT policy already exists: {policy_name}")

    return policy_name


def provision(robot_id: str, scp: bool):
    account, region = get_account_and_region()
    print(f"Account: {account}, Region: {region}")

    # Create Thing
    try:
        iot.create_thing(thingName=robot_id)
        print(f"Created IoT Thing: {robot_id}")
    except iot.exceptions.ResourceAlreadyExistsException:
        print(f"IoT Thing already exists: {robot_id}")

    # Create certificate
    cert_response = iot.create_keys_and_certificate(setAsActive=True)
    cert_arn = cert_response["certificateArn"]
    cert_id = cert_response["certificateId"]
    cert_pem = cert_response["certificatePem"]
    private_key = cert_response["keyPair"]["PrivateKey"]
    print(f"Created certificate: {cert_id[:12]}...")

    # Attach cert to Thing
    iot.attach_thing_principal(thingName=robot_id, principal=cert_arn)
    print(f"Attached certificate to Thing: {robot_id}")

    # Create and attach policy
    policy_name = create_policy(robot_id, account, region)
    iot.attach_policy(policyName=policy_name, target=cert_arn)
    print(f"Attached policy: {policy_name}")

    # Save cert files locally
    out_dir = os.path.join("certs", robot_id)
    os.makedirs(out_dir, exist_ok=True)

    cert_file = os.path.join(out_dir, "cert.pem")
    key_file = os.path.join(out_dir, "private.key")
    ca_file = os.path.join(out_dir, "AmazonRootCA1.pem")

    with open(cert_file, "w") as f:
        f.write(cert_pem)
    with open(key_file, "w") as f:
        f.write(private_key)

    urllib.request.urlretrieve(
        "https://www.amazontrust.com/repository/AmazonRootCA1.pem",
        ca_file,
    )

    print(f"\nCert bundle saved to {out_dir}/")
    print(f"  {cert_file}")
    print(f"  {key_file}")
    print(f"  {ca_file}")

    endpoint = iot.describe_endpoint(endpointType="iot:Data-ATS")["endpointAddress"]
    print(f"\nIoT Endpoint: {endpoint}")
    print(f"Set on robot: export X2_IOT_ENDPOINT={endpoint}")

    if scp:
        print(f"\nSCPing certs to X2:/home/run/x2_api/certs/ ...")
        subprocess.run(["ssh", "X2", "mkdir -p /home/run/x2_api/certs"], check=True)
        for fname in ["cert.pem", "private.key", "AmazonRootCA1.pem"]:
            src = os.path.join(out_dir, fname)
            subprocess.run(["scp", src, f"X2:/home/run/x2_api/certs/{fname}"], check=True)
        print("Done. Certs deployed to robot.")


def main():
    parser = argparse.ArgumentParser(description="Provision X2 robot as AWS IoT Thing")
    parser.add_argument("robot_id", help="Robot ID (e.g. x2-001)")
    parser.add_argument("--scp", action="store_true", help="SCP certs to robot via SSH alias X2")
    args = parser.parse_args()
    provision(args.robot_id, args.scp)


if __name__ == "__main__":
    main()
