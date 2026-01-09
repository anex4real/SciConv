from flask import request, jsonify
from functools import wraps

AUTH_TOKEN = "my-secret-token"

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token != f"Bearer {AUTH_TOKEN}":
            return jsonify({"message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated