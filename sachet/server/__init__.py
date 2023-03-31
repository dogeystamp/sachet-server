import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from .config import DevelopmentConfig, ProductionConfig, TestingConfig, overlay_config

app = Flask(__name__)
CORS(app)

if os.getenv("RUN_ENV") == "test":
    overlay_config(TestingConfig, "./config-testing.yml")
elif app.config["DEBUG"]:
    overlay_config(DevelopmentConfig)
    app.logger.warning("Running in DEVELOPMENT MODE; do NOT use this in production!")
else:
    overlay_config(ProductionConfig)

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
ma = Marshmallow()

import sachet.server.commands

from sachet.server.users.views import users_blueprint

app.register_blueprint(users_blueprint)

with app.app_context():
    db.create_all()
