import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from .config import DevelopmentConfig, ProductionConfig, TestingConfig, overlay_config
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection

app = Flask(__name__)
CORS(app)

with app.app_context():
    if os.getenv("RUN_ENV") == "test":
        overlay_config(TestingConfig, "./config-testing.yml")
    elif app.config["DEBUG"]:
        overlay_config(DevelopmentConfig)
        app.logger.warning(
            "Running in DEVELOPMENT MODE; do NOT use this in production!"
        )
    else:
        overlay_config(ProductionConfig)

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow()

_storage_method = app.config["SACHET_STORAGE"]

storage = None

from sachet.storage import FileSystem


# https://stackoverflow.com/questions/57726047/
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


with app.app_context():
    db.create_all()
    if _storage_method == "filesystem":
        storage = FileSystem()
    else:
        raise ValueError(f"{_storage_method} is not a valid storage method.")

import sachet.server.commands

from sachet.server.users.views import users_blueprint

app.register_blueprint(users_blueprint)

from sachet.server.admin.views import admin_blueprint

app.register_blueprint(admin_blueprint)

from sachet.server.files.views import files_blueprint

app.register_blueprint(files_blueprint)

from sachet.server.whoami.views import whoami_blueprint

app.register_blueprint(whoami_blueprint)
