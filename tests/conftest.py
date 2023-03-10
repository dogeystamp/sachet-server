import pytest
from click.testing import CliRunner

import os
os.environ["APP_SETTINGS"] = "sachet.server.config.TestingConfig"

from sachet.server import app, db

@pytest.fixture
def flask_app():
    """Flask application with DB already set up and ready."""
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            db.session.commit()
            yield app.test_client
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
def cli():
    """click's testing fixture"""
    return CliRunner()
