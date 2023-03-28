from sachet.server import app, db, ma, bcrypt
from marshmallow import fields, ValidationError
from flask import request, jsonify
from functools import wraps
import datetime
import jwt
from bitmask import Bitmask
from enum import IntFlag


class Permissions(IntFlag):
    CREATE = 1
    MODIFY = 1<<1
    DELETE = 1<<2
    LOCK = 1<<3
    LIST = 1<<4
    ADMIN = 1<<5


class User(db.Model):
    __tablename__ = "users"

    username = db.Column(db.String(255), unique=True, nullable=False, primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    register_date = db.Column(db.DateTime, nullable=False)

    permissions_number = db.Column(db.BigInteger, nullable=False, default=0)

    @property
    def permissions(self):
        """
        Bitmask listing all permissions.

        See the Permissions class for all possible permissions.
        
        Also, see https://github.com/dogeystamp/bitmask for information on how
        to use this field.
        """

        mask = Bitmask()
        mask.AllFlags = Permissions
        mask.value = self.permissions_number
        return mask

    @permissions.setter
    def permissions(self, value):
        mask = Bitmask()
        mask.AllFlags = Permissions
        mask += value
        self.permissions_number = mask.value
        db.session.commit()


    def __init__(self, username, password, permissions):
        permissions.AllFlags = Permissions
        self.permissions = permissions

        self.password = bcrypt.generate_password_hash(
                password, app.config.get("BCRYPT_LOG_ROUNDS")
        ).decode()
        self.username = username
        self.register_date = datetime.datetime.now()


    def encode_token(self, jti=None):
        """Generates an authentication token"""
        payload = {
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
            "iat": datetime.datetime.utcnow(),
            "sub": self.username,
            "jti": jti
        }
        return jwt.encode(
            payload,
            app.config.get("SECRET_KEY"),
            algorithm="HS256"
        )


class PermissionField(fields.Field):
    """Field that serializes a Permissions bitmask to an array of strings."""

    def _serialize(self, value, attr, obj, **kwargs):
        mask = Bitmask()
        mask.AllFlags = Permissions
        mask += value
        return [flag.name for flag in mask]

    def _deserialize(self, value, attr, data, **kwargs):
        mask = Bitmask()
        mask.AllFlags = Permissions

        flags = value

        try:
            for flag in flags:
                mask.add(Permissions[flag])
        except KeyError as e:
            raise ValidationError("Invalid permission.") from e

        return mask


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User

    username = ma.auto_field()
    register_date = ma.auto_field()
    permissions = PermissionField(data_key="permissions")


class BlacklistToken(db.Model):
    """Token that has been revoked (but has not expired yet.)

    This is needed to perform functionality like logging out.
    """

    __tablename__ = "blacklist_tokens"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(500), unique=True,  nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token

        data = jwt.decode(
            token,
            app.config["SECRET_KEY"],
            algorithms=["HS256"],
        )
        self.expires = datetime.datetime.fromtimestamp(data["exp"])

    @staticmethod
    def check_blacklist(token):
        """Returns if a token is blacklisted."""
        entry = BlacklistToken.query.filter_by(token=token).first()

        if not entry:
            return False
        else:
            if entry.expires < datetime.datetime.utcnow():
                db.session.delete(entry)
            return True


def read_token(token):
    """Read a JWT and validate it.

    Returns a tuple: dictionary of the JWT's data, and the corresponding user
    if available.
    """

    data = jwt.decode(
        token,
        app.config["SECRET_KEY"],
        algorithms=["HS256"],
    )

    if BlacklistToken.check_blacklist(token):
        raise jwt.ExpiredSignatureError("Token revoked.")

    user = User.query.filter_by(username=data.get("sub")).first()
    if not user:
        raise jwt.InvalidTokenError("No user corresponds to this token.")

    return data, user


def auth_required(f):
    """Decorator to require authentication.

    Passes an argument 'user' to the function, with a User object corresponding
    to the authenticated session.
    """
    @wraps(f)
    def decorator(*args, **kwargs):
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
            data, user = read_token(token)
        except jwt.ExpiredSignatureError:
            # if it's expired we don't want it lingering in the db
            BlacklistToken.check_blacklist(token)
            return jsonify({"status": "fail", "message": "Token has expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"status": "fail", "message": "Invalid auth token."}), 401

        return f(user, *args, **kwargs)

    return decorator
