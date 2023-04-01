from flask import request, jsonify
from flask.views import MethodView
from sachet.server.models import Permissions, User, BlacklistToken
from functools import wraps
from marshmallow import ValidationError
import jwt


def auth_required(func=None, *, require_admin=False):
    """Decorator to require authentication.

    Passes an argument 'user' to the function, with a User object corresponding
    to the authenticated session.
    """

    # see https://stackoverflow.com/questions/3888158/making-decorators-with-optional-arguments
    def _decorate(f):
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
                        "message": "Malformed Authorization header.",
                    }
                    return jsonify(resp), 401

            if not token:
                return jsonify({"status": "fail", "message": "Missing auth token"}), 401

            try:
                data, user = User.read_token(token)
            except jwt.ExpiredSignatureError:
                # if it's expired we don't want it lingering in the db
                BlacklistToken.check_blacklist(token)
                return jsonify({"status": "fail", "message": "Token has expired."}), 401
            except jwt.InvalidTokenError:
                return (
                    jsonify({"status": "fail", "message": "Invalid auth token."}),
                    401,
                )

            if require_admin and Permissions.ADMIN not in user.permissions:
                return (
                    jsonify(
                        {
                            "status": "fail",
                            "message": "Administrator permission is required to see this page.",
                        }
                    ),
                    403,
                )

            kwargs["auth_user"] = user
            return f(*args, **kwargs)

        return decorator

    if func:
        return _decorate(func)

    return _decorate


def patch(orig, diff):
    """Patch the dictionary orig recursively with the dictionary diff."""

    # if we get to a leaf node, just replace it
    if not isinstance(orig, dict) or not isinstance(diff, dict):
        return diff

    # deep copy
    new = {k: v for k, v in orig.items()}

    for key, value in diff.items():
        new[key] = patch(orig.get(key, {}), diff[key])

    return new


class ModelAPI(MethodView):
    """Generic REST API for interacting with models."""

    def get(self, model):
        return jsonify(model.get_schema().dump(model))

    def patch(self, model):
        model_schema = model.get_schema()

        if not model:
            resp = {
                "status": "fail",
                "message": "This resource does not exist.",
            }
            return jsonify(resp), 404

        patch_json = request.get_json()
        orig_json = model_schema.dump(model)

        new_json = patch(orig_json, patch_json)

        try:
            deserialized = model_schema.load(new_json)
        except ValidationError as e:
            resp = {"status": "fail", "message": f"Invalid patch: {str(e)}"}
            return jsonify(resp), 400

        for k, v in deserialized.items():
            setattr(model, k, v)

        resp = {
            "status": "success",
        }
        return jsonify(resp), 200

    def put(self, model):
        if not model:
            resp = {
                "status": "fail",
                "message": "This resource does not exist.",
            }
            return jsonify(resp), 404

        model_schema = model.get_schema()

        new_json = request.get_json()

        try:
            deserialized = model_schema.load(new_json)
        except ValidationError as e:
            resp = {"status": "fail", "message": f"Invalid data: {str(e)}"}
            return jsonify(resp), 400

        for k, v in deserialized.items():
            setattr(model, k, v)

        resp = {
            "status": "success",
        }
        return jsonify(resp), 200
