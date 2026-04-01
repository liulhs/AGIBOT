# x2_api/tests/test_auth.py
"""Tests for API key auth middleware."""
import os
import pytest
from flask import Flask
from auth import require_api_key


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True

    @app.route("/protected")
    @require_api_key
    def protected():
        return {"ok": True}

    @app.route("/health")
    def health():
        return {"ok": True}

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_request_without_key_returns_401(client):
    resp = client.get("/protected")
    assert resp.status_code == 401


def test_request_with_wrong_key_returns_403(client):
    resp = client.get("/protected", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 403


def test_request_with_correct_key_returns_200(client):
    key = os.environ.get("X2_API_KEY", "x2-dev-key-change-me")
    resp = client.get("/protected", headers={"X-API-Key": key})
    assert resp.status_code == 200


def test_health_endpoint_needs_no_key(client):
    resp = client.get("/health")
    assert resp.status_code == 200
