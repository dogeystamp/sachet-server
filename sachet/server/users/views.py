from flask import Blueprint, request, jsonify
from flask.views import MethodView
from sachet.server.models import token_required, admin_required, User
from sachet.server import bcrypt

users_blueprint = Blueprint("users_blueprint", __name__)

class LoginAPI(MethodView):
    def post(self):
        post_data = request.get_json()
        user = User.query.filter_by(username=post_data.get("username")).first()
        if not user:
            resp = {
                "status": "fail",
                "message": "Invalid credentials."
            }
            return jsonify(resp), 401

        if bcrypt.check_password_hash(
            user.password, post_data.get("password", "")
        ):
            token = user.encode_token()
            resp = {
                "status": "success",
                "message": "Logged in.",
                "username": user.username,
                "auth_token": token
            }
            return jsonify(resp), 200
        else:
            resp = {
                "status": "fail",
                "message": "Invalid credentials.",
            }
            return jsonify(resp), 401


users_blueprint.add_url_rule(
    "/users/login",
    view_func=LoginAPI.as_view("login_api"),
    methods=['POST']
)


class UserAPI(MethodView):
    """User information API"""
    @token_required
    def get(user, self, username):
        info_user = User.query.filter_by(username=username).first()
        if (not info_user) or (info_user != user and not user.admin):
            resp = {
                "status": "fail",
                "message": "You are not authorized to view this page."
            }
            return jsonify(resp), 403

        return jsonify({
            "username": info_user.username,
            "admin": info_user.admin,
        })

users_blueprint.add_url_rule(
    "/users/<username>",
    view_func=UserAPI.as_view("user_api"),
    methods=['GET']
)
