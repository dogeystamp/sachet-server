from sachet.server import db, ma, bcrypt, storage
import datetime
import jwt
from enum import IntFlag
from bitmask import Bitmask
from marshmallow import fields, ValidationError
from flask import request, jsonify, url_for, current_app
from sqlalchemy_utils import UUIDType
import uuid


class Permissions(IntFlag):
    CREATE = 1
    MODIFY = 1 << 1
    DELETE = 1 << 2
    LOCK = 1 << 3
    LIST = 1 << 4
    ADMIN = 1 << 5
    READ = 1 << 6


class PermissionField(fields.Field):
    """Field that serializes a Permissions bitmask to an array of strings in Marshmallow."""

    def _serialize(self, value, attr, obj, **kwargs):
        mask = Bitmask()
        mask.AllFlags = Permissions
        mask += value
        return [flag.name for flag in mask]

    def _deserialize(self, value, attr, data, **kwargs):
        mask = Bitmask()
        mask.AllFlags = Permissions

        flags = value

        try:
            for flag in flags:
                mask.add(Permissions[flag])
        except KeyError as e:
            raise ValidationError("Invalid permission.") from e

        return mask


class PermissionProperty:
    """
    Property to serialize/deserialize a Permissions Bitmask to an integer.

    The integer will have the same name as this property, suffixed with "_number".
    For example, use:

        class User(db.Model):
            permissions_number = db.Column(db.BigInteger, nullable=False, default=0)
            permissions = PermissionProperty()
    """

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        mask = Bitmask()
        mask.AllFlags = Permissions
        mask.value = getattr(obj, self.name + "_number")
        return mask

    def __set__(self, obj, value):
        mask = Bitmask()
        mask.AllFlags = Permissions
        mask += value
        setattr(obj, self.name + "_number", mask.value)
        db.session.commit()


class User(db.Model):
    __tablename__ = "users"

    username = db.Column(db.String(255), unique=True, nullable=False, primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    register_date = db.Column(db.DateTime, nullable=False)

    permissions_number = db.Column(db.BigInteger, nullable=False, default=0)
    permissions = PermissionProperty()

    def __init__(self, username, password, permissions):
        permissions.AllFlags = Permissions
        self.permissions = permissions

        self.password = bcrypt.generate_password_hash(
            password, current_app.config.get("BCRYPT_LOG_ROUNDS")
        ).decode()
        self.username = username
        self.register_date = datetime.datetime.now()

    def encode_token(self, jti=None):
        """Generates an authentication token"""
        payload = {
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
            "iat": datetime.datetime.utcnow(),
            "sub": self.username,
            "jti": jti,
        }
        return jwt.encode(
            payload, current_app.config.get("SECRET_KEY"), algorithm="HS256"
        )

    def read_token(token):
        """Read a JWT and validate it.

        Returns a tuple: dictionary of the JWT's data, and the corresponding user
        if available.
        """

        data = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=["HS256"],
        )

        if BlacklistToken.check_blacklist(token):
            raise jwt.ExpiredSignatureError("Token revoked.")

        user = User.query.filter_by(username=data.get("sub")).first()
        if not user:
            raise jwt.InvalidTokenError("No user corresponds to this token.")

        return data, user

    def get_schema(self):
        class Schema(ma.SQLAlchemySchema):
            class Meta:
                model = self

            username = ma.auto_field()
            register_date = ma.auto_field()
            permissions = PermissionField()

        return Schema()


class BlacklistToken(db.Model):
    """Token that has been revoked (but has not expired yet.)

    This is needed to perform functionality like logging out.
    """

    __tablename__ = "blacklist_tokens"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token

        data = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=["HS256"],
        )
        self.expires = datetime.datetime.fromtimestamp(data["exp"])

    @staticmethod
    def check_blacklist(token):
        """Returns if a token is blacklisted."""
        entry = BlacklistToken.query.filter_by(token=token).first()

        if not entry:
            return False
        else:
            if entry.expires < datetime.datetime.utcnow():
                db.session.delete(entry)
            return True


class ServerSettings(db.Model):
    __tablename__ = "server_settings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    default_permissions_number = db.Column(db.BigInteger, nullable=False, default=0)
    default_permissions = PermissionProperty()

    def __init__(self, default_permissions=Bitmask(AllFlags=Permissions)):
        self.default_permissions = default_permissions

    def get_schema(self):
        class Schema(ma.SQLAlchemySchema):
            class Meta:
                model = self

            default_permissions = PermissionField()

        return Schema()


def get_settings():
    """Return server settings, and create them if they don't exist."""
    rows = ServerSettings.query.all()
    if len(rows) == 0:
        settings = ServerSettings()
        db.session.add(settings)
        db.session.commit()
        return settings
    return rows[-1]


class Share(db.Model):
    """Share for a single file.

    Parameters
    ----------
    owner : User
        Assign this share to this user.

    Attributes
    ----------
    share_id : uuid.uuid4
        Unique identifier for this given share.
    owner : User
        The user who owns this share.
    initialized : bool
        Since only the metadata is uploaded first, this switches to True when
        the real data is uploaded.
    locked : bool
        Locks modification and deletion of this share.
    create_date : DateTime
        Time the share was created (not initialized.)
    file_name : str
        File name to download as.
    url : str
        URL linking to this object.

    Methods
    -------
    get_handle():
        Obtain a sachet.storage.Storage.File handle. This can be used to modify
        the file contents.
    """

    __tablename__ = "shares"

    share_id = db.Column(UUIDType(), primary_key=True, default=uuid.uuid4)

    owner_name = db.Column(db.String, db.ForeignKey("users.username"))
    owner = db.relationship("User", backref=db.backref("owner"))

    initialized = db.Column(db.Boolean, nullable=False, default=False)
    locked = db.Column(db.Boolean, nullable=False, default=False)

    create_date = db.Column(db.DateTime, nullable=False)

    file_name = db.Column(db.String, nullable=False)

    def __init__(self, owner_name=None, file_name=None, locked=False):
        self.owner = User.query.filter_by(username=owner_name).first()
        if self.owner:
            self.owner_name = self.owner.username
        self.share_id = uuid.uuid4()
        self.url = url_for("files_blueprint.files_metadata_api", share_id=self.share_id)
        self.create_date = datetime.datetime.now()
        if file_name:
            self.file_name = file_name
        else:
            self.file_name = str(self.share_id)

        self.locked = locked

    def get_schema(self):
        class Schema(ma.SQLAlchemySchema):
            class Meta:
                model = self

            share_id = ma.auto_field(dump_only=True)
            owner_name = ma.auto_field()
            file_name = ma.auto_field()
            initialized = ma.auto_field(dump_only=True)
            locked = ma.auto_field(dump_only=True)

        return Schema()

    def get_handle(self):
        return storage.get_file(str(self.share_id))


class Upload(db.Model):
    """Upload instance for a given file.

    Parameters
    ----------
    upload_id : str
        ID associated to this upload.
    total_chunks: int
        Total amount of chunks in this upload.
    share_id : uuid.UUID
        Assigns this upload to the given share id.

    Attributes
    ----------
    upload_id : str
        ID associated to this upload.
    total_chunks : int
        Total amount of chunks in this upload.
    recv_chunks : int
        Amount of chunks received in this upload.
    completed : bool
        Whether the file has been fully uploaded.
    share : Share
        The share this upload is for.
    chunks : list of Chunk
        Chunks composing this upload.
    create_date : DateTime
        Time this upload was started.
    """

    __tablename__ = "uploads"

    upload_id = db.Column(db.String, primary_key=True)

    share_id = db.Column(UUIDType(), db.ForeignKey("shares.share_id"))
    share = db.relationship("Share", backref=db.backref("upload"))
    create_date = db.Column(db.DateTime, nullable=False)
    total_chunks = db.Column(db.Integer, nullable=False)
    recv_chunks = db.Column(db.Integer, nullable=False, default=0)
    completed = db.Column(db.Boolean, nullable=False, default=False)

    chunks = db.relationship(
        "Chunk", backref=db.backref("upload"), order_by="Chunk.chunk_id"
    )

    def __init__(self, upload_id, total_chunks, share_id):
        self.share = Share.query.filter_by(share_id=share_id).first()
        if self.share is None:
            raise KeyError(f"Share '{self.share_id}' could not be found.")

        self.upload_id = upload_id
        self.total_chunks = total_chunks
        self.create_date = datetime.datetime.now()

    def complete(self):
        """Merge chunks, save the file, then clean up."""
        tmp_file = storage.get_file(f"{self.share.share_id}_{self.upload_id}")
        with tmp_file.open(mode="ab") as tmp_f:
            for chunk in self.chunks:
                chunk_file = storage.get_file(chunk.filename)
                with chunk_file.open(mode="rb") as chunk_f:
                    data = chunk_f.read()
                tmp_f.write(data)

        # replace the old file
        old_file = self.share.get_handle()
        old_file.delete()
        tmp_file.rename(str(self.share.share_id))

        self.completed = True


class Chunk(db.Model):
    """Single chunk within an upload.

    Parameters
    ----------
    index : int
        Index of this chunk within an upload.
    upload_id : str
        ID of the upload this chunk is associated to.
    total_chunks : int
        Total amount of chunks within this upload.
    share : Share
        Assigns this chunk to the given share.
    data : bytes
        Raw chunk data.

    Attributes
    ----------
    chunk_id : int
        ID unique for all chunks (not just in a single upload.)
    create_date : DateTime
        Time this chunk was received.
    index : int
        Index of this chunk within an upload.
    upload : Upload
        Upload this chunk is associated to.
    filename : str
        Filename the data is stored in.
    """

    __tablename__ = "chunks"

    chunk_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    create_date = db.Column(db.DateTime, nullable=False)
    index = db.Column(db.Integer, nullable=False)
    upload_id = db.Column(db.String, db.ForeignKey("uploads.upload_id"))
    filename = db.Column(db.String, nullable=False)

    def __init__(self, index, upload_id, total_chunks, share, data):
        self.upload = Upload.query.filter_by(upload_id=upload_id).first()
        if self.upload is None:
            self.upload = Upload(upload_id, total_chunks, share.share_id)
            self.upload.recv_chunks = 0
            db.session.add(self.upload)

        self.create_date = datetime.datetime.now()
        self.index = index
        self.filename = f"{share.share_id}_{self.upload_id}_{self.index}"

        file = storage.get_file(self.filename)
        with file.open(mode="wb") as f:
            f.write(data)
