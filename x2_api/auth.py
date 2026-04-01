# x2_api/auth.py
"""Simple API key authentication middleware for Flask."""
import os
from functools import wraps
from flask import request, jsonify
from config import API_KEY_HEADER, API_KEY


def _get_api_key() -> str:
    """Get API key from env or fall back to config default."""
    return os.environ.get("X2_API_KEY", API_KEY)


def require_api_key(f):
    """Decorator that checks for a valid API key in the request header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get(API_KEY_HEADER)
        if key is None:
            return jsonify({"error": "Missing API key", "header": API_KEY_HEADER}), 401
        if key != _get_api_key():
            return jsonify({"error": "Invalid API key"}), 403
        return f(*args, **kwargs)
    return decorated
