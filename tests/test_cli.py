import pytest
from sachet.server.commands import create_user, delete_user, cleanup
from sqlalchemy import inspect
from sachet.server import db
import datetime
from sachet.server.models import User, Share


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


def test_cleanup(client, cli):
    """Test the CLI's ability to destroy uninitialized shares past expiry."""
    # create shares
    # this one will be destroyed
    share = Share()
    db.session.add(share)
    share.create_date = datetime.datetime.now() - datetime.timedelta(minutes=30)
    destroyed = share.share_id
    # this one won't
    share = Share()
    db.session.add(share)
    safe = share.share_id
    # this one neither
    share = Share()
    share.initialized = True
    share.create_date = datetime.datetime.now() - datetime.timedelta(minutes=30)
    db.session.add(share)
    safe2 = share.share_id

    db.session.commit()

    result = cli.invoke(cleanup)
    assert result.exit_code == 0
    assert Share.query.filter_by(share_id=destroyed).first() is None
    assert Share.query.filter_by(share_id=safe).first() is not None
    assert Share.query.filter_by(share_id=safe2).first() is not None
