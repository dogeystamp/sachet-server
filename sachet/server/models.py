from sachet.server import app, db, bcrypt
import datetime

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    register_date = db.Column(db.DateTime, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, username, password, admin=False):
        self.password = bcrypt.generate_password_hash(
                password, app.config.get("BCRYPT_LOG_ROUNDS")
        ).decode()
        self.username = username
        self.register_date = datetime.datetime.now()
        self.admin = admin
