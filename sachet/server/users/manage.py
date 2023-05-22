from sachet.server import app, db
from sachet.server.models import User


def create_user(permissions, username, password):
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, password=password, permissions=permissions)
        db.session.add(user)
        db.session.commit()
    else:
        raise KeyError(f"User '{username}' already exists.")


def delete_user_by_username(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        raise KeyError(f"User {username} does not exist.")
    else:
        db.session.delete(user)
        db.session.commit()
