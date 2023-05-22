import uuid
import io
from flask import Blueprint, request, jsonify, send_file, make_response
from flask.views import MethodView
from sachet.server.models import Share, Permissions, Upload, Chunk
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
        if auth_user != share.owner:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": "Share must be modified by its owner.",
                    }
                ),
                403,
            )
        if share.locked:
            return jsonify({"status": "fail", "message": "This share is locked."}), 423
        return super().patch(share)

    @auth_required(required_permissions=(Permissions.MODIFY,), allow_anonymous=True)
    def put(self, share_id, auth_user=None):
        share = Share.query.filter_by(share_id=share_id).first()
        if auth_user != share.owner:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": "Share must be modified by its owner.",
                    }
                ),
                403,
            )
        if share.locked:
            return jsonify({"status": "fail", "message": "This share is locked."}), 423
        return super().put(share)

    @auth_required(required_permissions=(Permissions.DELETE,), allow_anonymous=True)
    def delete(self, share_id, auth_user=None):
        try:
            uuid.UUID(share_id)
        except ValueError:
            return jsonify(dict(status="fail", message=f"Invalid ID: '{share_id}'."))
        share = Share.query.filter_by(share_id=share_id).first()
        if share.locked:
            return jsonify({"status": "fail", "message": "This share is locked."}), 423
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


class FileContentAPI(MethodView):
    def recv_upload(self, share):
        """Receive chunked uploads.

        share : Share
            Share we are uploading to.
        """
        chunk_file = request.files.get("upload")
        if not chunk_file:
            return (
                jsonify(dict(status="fail", message="Missing chunk data in request.")),
                400,
            )
        chunk_data = chunk_file.read()

        try:
            dz_uuid = request.form["dzuuid"]
            dz_chunk_index = int(request.form["dzchunkindex"])
            dz_total_chunks = int(request.form["dztotalchunks"])
        except KeyError as err:
            return (
                jsonify(
                    dict(status="fail", message=f"Missing data for chunking; {err}")
                ),
                400,
            )
        except ValueError as err:
            return (
                jsonify(dict(status="fail", message=f"{err}")),
                400,
            )

        chunk = Chunk(dz_chunk_index, dz_uuid, dz_total_chunks, share, chunk_data)
        db.session.add(chunk)
        db.session.commit()
        upload = chunk.upload

        upload.recv_chunks = upload.recv_chunks + 1
        if upload.recv_chunks >= upload.total_chunks:
            upload.complete()

        if upload.completed:
            share.initialized = True
            db.session.delete(upload)
            db.session.commit()
            return jsonify(dict(status="success", message="Upload completed.")), 201
        else:
            return jsonify(dict(status="success", message="Chunk uploaded.")), 200

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

        return self.recv_upload(share)

    @auth_required(required_permissions=(Permissions.MODIFY,), allow_anonymous=True)
    def put(self, share_id, auth_user=None):
        share = Share.query.filter_by(share_id=share_id).first()
        if not share:
            return (
                jsonify({"status": "fail", "message": "This share does not exist."})
            ), 404

        if share.locked:
            return (
                jsonify({"status": "fail", "message": "This share is locked."})
            ), 423

        if auth_user != share.owner:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": "Share must be modified by its owner.",
                    }
                ),
                403,
            )

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

        return self.recv_upload(share)

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

        with file.open("rb") as f:
            resp = make_response(
                send_file(
                    io.BytesIO(f.read()),
                    download_name=share.file_name,
                    conditional=True,
                )
            )
            return resp


files_blueprint.add_url_rule(
    "/files/<share_id>/content",
    view_func=FileContentAPI.as_view("files_content_api"),
    methods=["POST", "PUT", "GET"],
)


class FileLockAPI(ModelAPI):
    @auth_required(required_permissions=(Permissions.LOCK,), allow_anonymous=True)
    def post(self, share_id, auth_user=None):
        share = Share.query.filter_by(share_id=uuid.UUID(share_id)).first()
        if not share:
            return (
                jsonify({"status": "fail", "message": "This share does not exist."})
            ), 404

        share.locked = True
        db.session.commit()

        return jsonify({"status": "success", "message": "Share has been locked."})


files_blueprint.add_url_rule(
    "/files/<share_id>/lock",
    view_func=FileLockAPI.as_view("files_lock_api"),
    methods=["POST"],
)


class FileUnlockAPI(ModelAPI):
    @auth_required(required_permissions=(Permissions.LOCK,), allow_anonymous=True)
    def post(self, share_id, auth_user=None):
        share = Share.query.filter_by(share_id=uuid.UUID(share_id)).first()
        if not share:
            return (
                jsonify({"status": "fail", "message": "This share does not exist."})
            ), 404

        share.locked = False
        db.session.commit()

        return jsonify({"status": "success", "message": "Share has been unlocked."})


files_blueprint.add_url_rule(
    "/files/<share_id>/unlock",
    view_func=FileUnlockAPI.as_view("files_unlock_api"),
    methods=["POST"],
)
