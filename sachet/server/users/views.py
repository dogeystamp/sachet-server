import jwt
from flask import Blueprint, request, jsonify
from flask.views import MethodView
from sachet.server.models import (
    auth_required,
    read_token,
    patch,
    Permissions,
    User,
    UserSchema,
    BlacklistToken,
)
from sachet.server import bcrypt, db
from marshmallow import ValidationError

user_schema = UserSchema()

users_blueprint = Blueprint("users_blueprint", __name__)


class LoginAPI(MethodView):
    def post(self):
        post_data = request.get_json()
        user = User.query.filter_by(username=post_data.get("username")).first()
        if not user:
            resp = {"status": "fail", "message": "Invalid credentials."}
            return jsonify(resp), 401

        if bcrypt.check_password_hash(user.password, post_data.get("password", "")):
            token = user.encode_token()
            resp = {
                "status": "success",
                "message": "Logged in.",
                "username": user.username,
                "auth_token": token,
            }
            return jsonify(resp), 200
        else:
            resp = {
                "status": "fail",
                "message": "Invalid credentials.",
            }
            return jsonify(resp), 401


users_blueprint.add_url_rule(
    "/users/login", view_func=LoginAPI.as_view("login_api"), methods=["POST"]
)


class LogoutAPI(MethodView):
    """Endpoint to revoke a user's token."""

    @auth_required
    def post(user, self):
        post_data = request.get_json()
        token = post_data.get("token")
        if not token:
            return (
                jsonify({"status": "fail", "message": "Specify a token to revoke."}),
                400,
            )

        res = BlacklistToken.check_blacklist(token)
        if res:
            return jsonify({"status": "fail", "message": "Token already revoked."}), 400

        try:
            data, token_user = read_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"status": "fail", "message": "Token already expired."}), 400
        except jwt.InvalidTokenError:
            return jsonify({"status": "fail", "message": "Invalid auth token."}), 400

        if user == token_user or Permissions.ADMIN in user.permissions:
            entry = BlacklistToken(token=token)
            db.session.add(entry)
            db.session.commit()
            return jsonify({"status": "success", "message": "Token revoked."}), 200
        else:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": "You are not allowed to revoke this token.",
                    }
                ),
                403,
            )


users_blueprint.add_url_rule(
    "/users/logout", view_func=LogoutAPI.as_view("logout_api"), methods=["POST"]
)


class ExtendAPI(MethodView):
    """Endpoint to take a token and get a new one with a later expiry date."""

    @auth_required
    def post(user, self):
        token = user.encode_token(jti="renew")
        resp = {
            "status": "success",
            "message": "Renewed token.",
            "username": user.username,
            "auth_token": token,
        }
        return jsonify(resp), 200


users_blueprint.add_url_rule(
    "/users/extend", view_func=ExtendAPI.as_view("extend_api"), methods=["POST"]
)


class UserAPI(MethodView):
    """User information API"""

    @auth_required
    def get(user, self, username):
        info_user = User.query.filter_by(username=username).first()
        if (not info_user) or (
            info_user != user and Permissions.ADMIN not in user.permissions
        ):
            resp = {
                "status": "fail",
                "message": "You are not authorized to view this page.",
            }
            return jsonify(resp), 403

        return jsonify(user_schema.dump(info_user))

    @auth_required
    def patch(user, self, username):
        patch_user = User.query.filter_by(username=username).first()

        if not patch_user or Permissions.ADMIN not in user.permissions:
            resp = {
                "status": "fail",
                "message": "You are not authorized to access this page.",
            }
            return jsonify(resp), 403

        patch_json = request.get_json()
        orig_json = user_schema.dump(patch_user)

        new_json = patch(orig_json, patch_json)

        try:
            deserialized = user_schema.load(new_json)
        except ValidationError as e:
            resp = {"status": "fail", "message": f"Invalid patch: {str(e)}"}
            return jsonify(resp), 400

        for k, v in deserialized.items():
            setattr(patch_user, k, v)

        resp = {
            "status": "success",
        }
        return jsonify(resp), 200

    @auth_required
    def put(user, self, username):
        put_user = User.query.filter_by(username=username).first()

        if not put_user or Permissions.ADMIN not in user.permissions:
            resp = {
                "status": "fail",
                "message": "You are not authorized to access this page.",
            }
            return jsonify(resp), 403

        new_json = request.get_json()

        try:
            deserialized = user_schema.load(new_json)
        except ValidationError as e:
            resp = {"status": "fail", "message": f"Invalid data: {str(e)}"}
            return jsonify(resp), 400

        for k, v in deserialized.items():
            setattr(put_user, k, v)

        resp = {
            "status": "success",
        }
        return jsonify(resp), 200


users_blueprint.add_url_rule(
    "/users/<username>",
    view_func=UserAPI.as_view("user_api"),
    methods=["GET", "PATCH", "PUT"],
)
