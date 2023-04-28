from flask import Blueprint, request, jsonify
from flask.views import MethodView
from sachet.server.models import ServerSettings, get_settings, Permissions
from sachet.server import db
from sachet.server.views_common import auth_required, ModelAPI


admin_blueprint = Blueprint("admin_blueprint", __name__)


class ServerSettingsAPI(ModelAPI):
    @auth_required(required_permissions=(Permissions.ADMIN,))
    def get(self, auth_user=None):
        settings = get_settings()
        return super().get(settings)

    @auth_required(required_permissions=(Permissions.ADMIN,))
    def patch(self, auth_user=None):
        settings = get_settings()
        return super().patch(settings)

    @auth_required(required_permissions=(Permissions.ADMIN,))
    def put(self, auth_user=None):
        settings = get_settings()
        return super().put(settings)


admin_blueprint.add_url_rule(
    "/admin/settings",
    view_func=ServerSettingsAPI.as_view("server_settings_api"),
    methods=["PATCH", "GET", "PUT"],
)
