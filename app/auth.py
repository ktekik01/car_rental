from functools import wraps
from flask import request, jsonify, current_app
from app.models import User
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from app.extensions import db
from flask import Blueprint



auth_bp = Blueprint('auth', __name__)

# Basic Auth decorator
def basic_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return jsonify({"error": "missing credentials"}), 401
        user = User.query.filter_by(username=auth.username).first()
        if not user or not check_password_hash(user.password, auth.password):
            return jsonify({"error": "invalid credentials"}), 401
        request.current_user = user
        return f(*args, **kwargs)
    return decorated

# Role check decorator
def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(request, 'current_user', None)
            if not user or user.role not in roles:
                return jsonify({"error": "forbidden"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# User registration endpoint
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    role     = data.get("role", "user")

    # 1) basic validation
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    # 2) enforce allowed roles
    if role not in ("user", "merchant"):
        return jsonify({"error": "invalid role"}), 400

    # 3) username uniqueness
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username taken"}), 400

    # 4) create the user
    user = User(
        username=username,
        password=generate_password_hash(password),
        role=role
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "registered",
        "role": role
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth:
        return jsonify({"error":"missing credentials"}), 401
    user = User.query.filter_by(username=auth.username).first()
    if not user or not check_password_hash(user.password, auth.password):
        return jsonify({"error":"invalid credentials"}), 401
    return jsonify({"message": f"welcome, {user.username}"})
