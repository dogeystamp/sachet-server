from flask import request, jsonify
from flask.views import MethodView
from sachet.server.models import Permissions, User, BlacklistToken, get_settings
from sachet.server import db
from functools import wraps
from marshmallow import ValidationError
from bitmask import Bitmask
import jwt


# https://stackoverflow.com/questions/3888158/making-decorators-with-optional-arguments
def auth_required(func=None, *, required_permissions=(), allow_anonymous=False):
    """Require specific authentication.

    Passes an argument `user` to the function, with a User object corresponding
    to the authenticated session.

    Parameters
    ----------
    required_permissions : tuple of Permissions, optional
        Permissions required to access this endpoint.
    allow_anonymous : bool, optional
        Allow anonymous authentication. This means the `user` parameter might be None.
    """

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
                if allow_anonymous:
                    server_settings = get_settings()
                    if (
                        Bitmask(AllFlags=Permissions, *required_permissions)
                        not in server_settings.default_permissions
                    ):
                        return (
                            jsonify(
                                {
                                    "status": "fail",
                                    "message": "Missing permissions to access this page.",
                                }
                            ),
                            401,
                        )
                    kwargs["auth_user"] = None
                    return f(*args, **kwargs)
                else:
                    return (
                        jsonify({"status": "fail", "message": "Missing auth token"}),
                        401,
                    )

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

            if (
                Bitmask(AllFlags=Permissions, *required_permissions)
                not in user.permissions
            ):
                return (
                    jsonify(
                        {
                            "status": "fail",
                            "message": "Missing permissions to access this page.",
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
    """Generic REST API for the representation of a model instance."""

    def get(self, model):
        if not model:
            resp = {
                "status": "fail",
                "message": "This resource does not exist.",
            }
            return jsonify(resp), 404

        return jsonify(model.get_schema().dump(model))

    def patch(self, model):
        if not model:
            resp = {
                "status": "fail",
                "message": "This resource does not exist.",
            }
            return jsonify(resp), 404

        model_schema = model.get_schema()

        if not model:
            resp = {
                "status": "fail",
                "message": "This resource does not exist.",
            }
            return jsonify(resp), 404

        patch_json = request.get_json()

        dump = model_schema.dump(model)
        orig_json = {}
        for field, opts in model_schema.fields.items():
            if not opts.dump_only and not opts.load_only:
                orig_json[field] = dump[field]

        new_json = patch(orig_json, patch_json)

        try:
            deserialized = model_schema.load(new_json)
        except ValidationError as e:
            resp = {"status": "fail", "message": f"Invalid patch: {str(e)}"}
            return jsonify(resp), 400

        for k, v in deserialized.items():
            setattr(model, k, v)

        db.session.commit()

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

        db.session.commit()

        resp = {
            "status": "success",
        }
        return jsonify(resp), 200

    def delete(self, model):
        if not model:
            resp = {
                "status": "fail",
                "message": "This resource does not exist.",
            }
            return jsonify(resp), 404

        db.session.delete(model)
        db.session.commit()

        return jsonify({"status": "success"})


class ModelListAPI(MethodView):
    """Generic API for representing all instances of a given model."""

    def post(self, ModelClass, data={}):
        """Create new instance of a class.

        Parameters
        ----------
        ModelClass
            Class to make an instance of.
        data : dict
            Object that can be loaded with Marshmallow to create the class.
        """
        model_schema = ModelClass.get_schema(ModelClass)

        try:
            deserialized = model_schema.load(data)
        except ValidationError as e:
            resp = {"status": "fail", "message": f"Invalid data: {str(e)}"}
            return jsonify(resp), 400

        # create new ModelClass instance with all the parameters given in the request
        model = ModelClass(**deserialized)

        db.session.add(model)
        db.session.commit()

        return jsonify({"status": "success", "url": model.url}), 201

    def get(self, ModelClass):
        """List a given range of instances.

        Parameters
        ----------
        ModelClass
            Model class to query.

        URL Parameters
        ---------------
        per_page : int
            Amount of entries to return in one query.
        page : int
            Incrementing this reads the next `per_page` entries.

        Returns
        -------
        data : list of dict
            All requested entries.
        prev : int or None
            Number of previous page (if this is not the first).
        next : int or None
            Number of next page (if this is not the last).
        pages : int
            Total number of pages.
        """
        try:
            per_page = int(request.args.get("per_page", 15))
            page = int(request.args.get("page", 1))
        except ValueError as e:
            return (
                jsonify(
                    dict(
                        status="fail",
                        message=str(e),
                    )
                ),
                400,
            )

        page_data = ModelClass.query.paginate(page=page, per_page=per_page)
        data = [model.get_schema().dump(model) for model in page_data]

        return jsonify(
            dict(
                data=data,
                prev=page_data.prev_num,
                next=page_data.next_num,
                pages=page_data.pages,
            )
        )
