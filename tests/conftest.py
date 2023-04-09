import pytest
import yaml
from sachet.server.users import manage
from click.testing import CliRunner
from sachet.server import app, db, storage
from sachet.server.models import Permissions, User
from bitmask import Bitmask
from pathlib import Path
import random
import itertools


@pytest.fixture
def rand():
    """Deterministic random data generator.

    Be sure to seed 0 with each test!
    """
    r = random.Random()
    r.seed(0)
    return r


def clear_filesystem():
    if app.config["SACHET_STORAGE"] == "filesystem":
        for file in itertools.chain(
            storage._meta_directory.iterdir(),
            storage._files_directory.iterdir(),
        ):
            if file.is_relative_to(Path(app.instance_path)) and file.is_file():
                file.unlink()
            else:
                raise OSError(f"Attempted to delete {file}: please delete it yourself.")


@pytest.fixture
def client(config={}):
    """Flask application with DB already set up and ready."""
    with app.test_client() as client:
        with app.app_context():
            for k, v in config.items():
                app.config[k] = v

            db.drop_all()
            db.create_all()
            db.session.commit()
            clear_filesystem()
            yield client
            clear_filesystem()
            db.session.remove()
            db.drop_all()


@pytest.fixture
def flask_app_bare():
    """Flask application with empty DB."""
    with app.test_client() as client:
        with app.app_context():
            yield client
            db.drop_all()


@pytest.fixture
def users(client):
    """Creates all the test users.

    Returns a dictionary with all the info for each user.
    """
    userinfo = dict(
        jeff=dict(password="1234", permissions=Bitmask()),
        administrator=dict(password="4321", permissions=Bitmask(Permissions.ADMIN)),
    )

    for user, info in userinfo.items():
        info["username"] = user
        manage.create_user(info["permissions"], info["username"], info["password"])

    return userinfo


@pytest.fixture
def validate_info(users):
    """Given a response, deserialize and validate the information against a given user's info."""

    verify_fields = [
        "username",
        "permissions",
    ]

    def _validate(user, info):
        info = User.get_schema(User).load(info)

        for k in verify_fields:
            assert users[user][k] == info[k]

    return _validate


@pytest.fixture
def tokens(client, users):
    """Logs in all test users.

    Returns a dictionary of auth tokens for all test users.
    """

    toks = {}

    for user, creds in users.items():
        resp = client.post(
            "/users/login",
            json={"username": creds["username"], "password": creds["password"]},
        )
        resp_json = resp.get_json()
        token = resp_json.get("auth_token")
        assert token is not None and token != ""
        toks[creds["username"]] = token

    return toks


@pytest.fixture
def cli():
    """click's testing fixture"""
    return CliRunner()
