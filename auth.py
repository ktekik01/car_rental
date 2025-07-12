# auth.py
from functools import wraps
from flask import request, jsonify
from werkzeug.security import check_password_hash
from models import User

def basic_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return jsonify({"error": "Missing credentials"}), 401

        user = User.query.filter_by(username=auth.username).first()
        if not user or not check_password_hash(user.password, auth.password):
            return jsonify({"error": "Invalid credentials"}), 401

        request.current_user = user
        return f(*args, **kwargs)
    return decorated


def roles_required(*allowed_roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.current_user.role not in allowed_roles:
                return jsonify({"error": "forbidden"}), 403
            return f(*args, **kwargs)
        return decorated
    return wrapper
