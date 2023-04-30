import click
from sachet.server import app, db
from sachet.server.models import User, Share, Permissions
from sachet.server.users import manage
from flask.cli import AppGroup
from bitmask import Bitmask
import datetime


user_cli = AppGroup("user")


@user_cli.command("create")
@click.option(
    "--admin",
    default=False,
    prompt="Set this user as administrator?",
    help="Set this user an administrator.",
)
@click.option("--username", prompt="Username", help="Sets the username.")
@click.option(
    "--password",
    prompt="Password",
    hide_input=True,
    help="Sets the user's password (for security, avoid setting this from the command line).",
)
def create_user(admin, username, password):
    """Create a user directly in the database."""
    perms = Bitmask()
    if admin:
        perms.add(Permissions.ADMIN)
    manage.create_user(perms, username, password)


@user_cli.command("delete")
@click.argument("username")
@click.option(
    "--yes",
    is_flag=True,
    expose_value=False,
    prompt=f"Are you sure you want to delete this user?",
)
def delete_user(username):
    manage.delete_user_by_username(username)


app.cli.add_command(user_cli)


@user_cli.command("cleanup")
def cleanup():
    """Clean up stale database entries.

    Shares that are not initialized are deleted if they are older than 25 minutes.
    """
    res = Share.query.filter(
        Share.create_date < (datetime.datetime.now() - datetime.timedelta(minutes=25)),
        # do not use `Share.initialized` or `is False` here
        # sqlalchemy doesn't like it
        Share.initialized == False,
    )
    res.delete()
    db.session.commit()


app.cli.add_command(cleanup)
