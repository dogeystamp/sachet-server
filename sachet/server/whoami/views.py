from flask import Blueprint, request, jsonify
from flask.views import MethodView
from sachet.server.models import User, ServerSettings, get_settings
from sachet.server.views_common import auth_required

whoami_blueprint = Blueprint("whoami_blueprint", __name__)


class WhoamiAPI(MethodView):
    @auth_required(allow_anonymous=True)
    def get(self, auth_user=None):
        if auth_user:
            data = auth_user.get_schema().dump(auth_user)
            username = data.get("username")
            perms = data.get("permissions")
        else:
            username = None
            model = get_settings()
            data = model.get_schema().dump(model)
            perms = data.get("default_permissions")

        return jsonify(dict(username=username, permissions=perms))


whoami_blueprint.add_url_rule(
    "/whoami", view_func=WhoamiAPI.as_view("whoami_api"), methods=["GET"]
)
