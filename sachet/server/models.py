from sachet.server import app, db, bcrypt
from flask import request, jsonify
from functools import wraps
import datetime
import jwt

class User(db.Model):
    __tablename__ = "users"

    username = db.Column(db.String(255), unique=True, nullable=False, primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    register_date = db.Column(db.DateTime, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, username, password, admin=False):
        self.password = bcrypt.generate_password_hash(
                password, app.config.get("BCRYPT_LOG_ROUNDS")
        ).decode()
        self.username = username
        self.register_date = datetime.datetime.now()
        self.admin = admin

    def encode_token(self):
        """Generates an authentication token"""
        payload = {
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
            "iat": datetime.datetime.utcnow(),
            "sub": self.username
        }
        return jwt.encode(
            payload,
            app.config.get("SECRET_KEY"),
            algorithm="HS256"
        )

def _token_decorator(require_admin, f, *args, **kwargs):
    """Generic function for checking tokens.

    require_admin: require user to be administrator to authenticate
    """
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            resp = {
                "status": "fail",
                "message": "Malformed Authorization header."
            }
            return jsonify(resp), 401

    if not token:
        return jsonify({"status": "fail", "message": "Missing auth token"}), 401
    try:
        data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        user = User.query.filter_by(username=data.get("sub")).first()
    except:
        return jsonify({"status": "fail", "message": "Invalid auth token."}), 401

    if not user:
        return jsonify({"status": "fail", "message": "Invalid auth token."}), 401

    if require_admin and not user.admin:
        return jsonify({"status": "fail", "message": "You are not authorized to view this page."}), 403

    return f(user, *args, **kwargs)

def token_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorator(*args, **kwargs):
        return _token_decorator(False, f, *args, **kwargs)
    return decorator

def admin_required(f):
    """Decorator to require authentication and admin privileges."""

    @wraps(f)
    def decorator(*args, **kwargs):
        return _token_decorator(True, f, *args, **kwargs)
    return decorator
