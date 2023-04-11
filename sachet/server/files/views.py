import jwt
from flask import Blueprint, request, jsonify
from flask.views import MethodView
from sachet.server.models import File, Permissions
from sachet.server.views_common import ModelAPI, auth_required

files_blueprint = Blueprint("files_blueprint", __name__)


class FilesAPI(ModelAPI):
    """Files metadata API."""

    @auth_required
    def get(self, id, auth_user=None):
        pass


files_blueprint.add_url_rule(
    "/files/<id>",
    view_func=FilesAPI.as_view("files_api"),
    methods=["POST", "PUT", "PATCH", "GET", "DELETE"],
)

files_blueprint.add_url_rule(
    "/files/<id>/content",
    view_func=FilesContentAPI.as_view("files_content_api"),
    methods=["PUT", "GET"],
)


users_blueprint.add_url_rule(
    "/users/<username>",
    view_func=UserAPI.as_view("user_api"),
    methods=["GET", "PATCH", "PUT"],
)
