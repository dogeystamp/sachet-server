import jwt
from flask import Blueprint, request, jsonify
from flask.views import MethodView
from sachet.server.models import (
    Permissions,
    User,
    BlacklistToken,
)
from sachet.server.views_common import ModelAPI, auth_required
from sachet.server import bcrypt, db

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
    def post(self, auth_user=None):
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
            data, token_user = User.read_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"status": "fail", "message": "Token already expired."}), 400
        except jwt.InvalidTokenError:
            return jsonify({"status": "fail", "message": "Invalid auth token."}), 400

        if auth_user == token_user or Permissions.ADMIN in auth_user.permissions:
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
    def post(self, auth_user=None):
        token = auth_user.encode_token(jti="renew")
        resp = {
            "status": "success",
            "message": "Renewed token.",
            "username": auth_user.username,
            "auth_token": token,
        }
        return jsonify(resp), 200


users_blueprint.add_url_rule(
    "/users/extend", view_func=ExtendAPI.as_view("extend_api"), methods=["POST"]
)


class UserAPI(ModelAPI):
    """User information API"""

    @auth_required
    def get(self, username, auth_user=None):
        info_user = User.query.filter_by(username=username).first()
        # only allow user to query themselves, but admin can query anyone
        if (not info_user) or (
            info_user != auth_user and Permissions.ADMIN not in auth_user.permissions
        ):
            resp = {
                "status": "fail",
                "message": "You are not authorized to view this page.",
            }
            return jsonify(resp), 403

        return super().get(info_user)

    @auth_required(required_permissions=(Permissions.ADMIN,))
    def patch(self, username, auth_user=None):
        patch_user = User.query.filter_by(username=username).first()
        return super().patch(patch_user)

    @auth_required(required_permissions=(Permissions.ADMIN,))
    def put(self, username, auth_user=None):
        put_user = User.query.filter_by(username=username).first()
        return super().put(put_user)


users_blueprint.add_url_rule(
    "/users/<username>",
    view_func=UserAPI.as_view("user_api"),
    methods=["GET", "PATCH", "PUT"],
)
