import pytest
from sachet.server.commands import create_user, delete_user
from sqlalchemy import inspect

from sachet.server.models import User


def test_user(client, cli):
    """Test the CLI's ability to create then delete a user."""
    # create user
    result = cli.invoke(create_user, ["--username", "jeff", "--password", "1234"])
    assert result.exit_code == 0
    assert User.query.filter_by(username="jeff").first() is not None

    # create duplicate user
    result = cli.invoke(create_user, ["--username", "jeff", "--password", "1234"])
    assert isinstance(result.exception, KeyError)

    # delete user
    result = cli.invoke(delete_user, ["--yes", "jeff"])
    assert result.exit_code == 0
    assert User.query.filter_by(username="jeff").first() is None

    # delete non-existent user
    result = cli.invoke(delete_user, ["--yes", "jeff"])
    assert isinstance(result.exception, KeyError)
