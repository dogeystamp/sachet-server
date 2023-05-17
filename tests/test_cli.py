import pytest
from sachet.server.commands import create_user, delete_user, cleanup
from sqlalchemy import inspect
from sachet.server import db
import datetime
from sachet.server.models import User, Share, Chunk, Upload


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
    """Test the CLI's ability to destroy stale entries."""
    # create shares
    # this one will be destroyed
    share = Share()
    db.session.add(share)
    share.create_date = datetime.datetime.now() - datetime.timedelta(hours=30)
    destroyed = share.share_id
    # this one won't
    share = Share()
    db.session.add(share)
    safe = share.share_id
    # this one neither
    share = Share()
    share.initialized = True
    share.create_date = datetime.datetime.now() - datetime.timedelta(hours=30)
    db.session.add(share)
    safe2 = share.share_id

    db.session.commit()

    result = cli.invoke(cleanup)
    assert result.exit_code == 0
    assert Share.query.filter_by(share_id=destroyed).first() is None
    assert Share.query.filter_by(share_id=safe).first() is not None
    assert Share.query.filter_by(share_id=safe2).first() is not None

    # test stale uploads and chunks

    test_share = Share()
    db.session.add(test_share)

    chk = Chunk(0, "upload1", 1, test_share, b"test_data")
    chk.upload.create_date = datetime.datetime.now() - datetime.timedelta(hours=30)
    db.session.add(chk)
    chk_upload_id = chk.upload.upload_id

    chk_safe = Chunk(0, "upload2", 1, test_share, b"test_data")
    db.session.add(chk_safe)
    chk_safe_upload_id = chk_safe.upload.upload_id

    db.session.commit()

    chk_id = chk.chunk_id
    chk_safe_id = chk_safe.chunk_id

    result = cli.invoke(cleanup)
    assert result.exit_code == 0
    assert Chunk.query.filter_by(chunk_id=chk_id).first() is None
    assert Chunk.query.filter_by(chunk_id=chk_safe_id).first() is not None
    assert Upload.query.filter_by(upload_id=chk_upload_id).first() is None
    assert Upload.query.filter_by(upload_id=chk_safe_upload_id).first() is not None
