import uuid
import io
from flask import Blueprint, request, jsonify, send_file
from flask.views import MethodView
from sachet.server.models import Share, Permissions
from sachet.server.views_common import ModelAPI, ModelListAPI, auth_required
from sachet.server import storage, db

files_blueprint = Blueprint("files_blueprint", __name__)


class FilesMetadataAPI(ModelAPI):
    @auth_required(required_permissions=(Permissions.READ,), allow_anonymous=True)
    def get(self, share_id, auth_user=None):
        share = Share.query.filter_by(share_id=share_id).first()
        return super().get(share)

    @auth_required(required_permissions=(Permissions.MODIFY,), allow_anonymous=True)
    def patch(self, share_id, auth_user=None):
        share = Share.query.filter_by(share_id=share_id).first()
        return super().patch(share)

    @auth_required(required_permissions=(Permissions.MODIFY,), allow_anonymous=True)
    def put(self, share_id, auth_user=None):
        share = Share.query.filter_by(share_id=share_id).first()
        return super().put(share)

    @auth_required(required_permissions=(Permissions.DELETE,), allow_anonymous=True)
    def delete(self, share_id, auth_user=None):
        try:
            uuid.UUID(share_id)
        except ValueError:
            return jsonify(dict(status="fail", message=f"Invalid ID: '{share_id}'."))
        share = Share.query.filter_by(share_id=share_id).first()
        return super().delete(share)


files_blueprint.add_url_rule(
    "/files/<share_id>",
    view_func=FilesMetadataAPI.as_view("files_metadata_api"),
    methods=["PUT", "PATCH", "GET", "DELETE"],
)


class FilesAPI(ModelListAPI):
    @auth_required(required_permissions=(Permissions.CREATE,), allow_anonymous=True)
    def post(self, auth_user=None):
        data = request.get_json()
        if auth_user:
            data["owner_name"] = auth_user.username
        return super().post(Share, data)

    @auth_required(required_permissions=(Permissions.LIST,), allow_anonymous=True)
    def get(self, auth_user=None):
        return super().get(Share)


files_blueprint.add_url_rule(
    "/files",
    view_func=FilesAPI.as_view("files_api"),
    methods=["POST", "GET"],
)


class FileContentAPI(ModelAPI):
    @auth_required(required_permissions=(Permissions.CREATE,), allow_anonymous=True)
    def post(self, share_id, auth_user=None):
        share = Share.query.filter_by(share_id=uuid.UUID(share_id)).first()

        if not share:
            return (
                jsonify({"status": "fail", "message": "This share does not exist."})
            ), 404

        if auth_user != share.owner:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": "Share must be initialized by its owner.",
                    }
                ),
                403,
            )

        if share.initialized:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": "Share already initialized. Use PUT to modify the share.",
                    }
                ),
                423,
            )

        upload = request.files["upload"]
        data = upload.read()
        file = share.get_handle()
        with file.open(mode="wb") as f:
            f.write(data)

        share.initialized = True

        db.session.commit()

        return (
            jsonify({"status": "success", "message": "Share has been initialized."}),
            201,
        )

    @auth_required(required_permissions=(Permissions.MODIFY,), allow_anonymous=True)
    def put(self, share_id, auth_user=None):
        share = Share.query.filter_by(share_id=share_id).first()
        if not share:
            return (
                jsonify({"status": "fail", "message": "This share does not exist."})
            ), 404

        if not share.initialized:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": "Share not initialized. Use POST to upload for the first time to this share.",
                    }
                ),
                423,
            )

        upload = request.files["upload"]
        data = upload.read()
        file = share.get_handle()

        with file.open(mode="wb") as f:
            f.write(data)

        return (
            jsonify({"status": "success", "message": "Share has been modified."}),
            200,
        )

    @auth_required(required_permissions=(Permissions.READ,), allow_anonymous=True)
    def get(self, share_id, auth_user=None):
        share = Share.query.filter_by(share_id=share_id).first()
        if not share:
            return (
                jsonify({"status": "fail", "message": "This share does not exist."})
            ), 404

        if not share.initialized:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": "Share not initialized. Use POST to upload for the first time to this share.",
                    }
                ),
                404,
            )

        file = share.get_handle()
        with file.open(mode="rb") as f:
            data = f.read()

        return send_file(io.BytesIO(data), download_name=share.file_name)


files_blueprint.add_url_rule(
    "/files/<share_id>/content",
    view_func=FileContentAPI.as_view("files_content_api"),
    methods=["POST", "PUT", "GET"],
)
