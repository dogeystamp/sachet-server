import click
from sachet.server import app, db
from sachet.server.models import User
from flask.cli import AppGroup


db_cli = AppGroup("db")

@db_cli.command("create")
def create_db():
    """Create all db tables."""
    db.create_all()


@db_cli.command("drop")
@click.option('--yes', is_flag=True, expose_value=False, prompt="Are you sure you want to drop all tables?")
def drop_db():
    """Drop all db tables."""
    db.drop_all()

app.cli.add_command(db_cli)


user_cli = AppGroup("user")

@user_cli.command("create")
@click.option("--admin", default=False, prompt="Set this user as administrator?", help="Set this user an administrator.")
@click.option("--username", prompt="Username", help="Sets the username.")
@click.option("--password",
              prompt="Password",
              hide_input=True,
              help="Sets the user's password (for security, avoid setting this from the command line).")
def create_user(admin, username, password):
    """Create a user directly in the database."""
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            password=password,
            admin=admin
        )
        db.session.add(user)
        db.session.commit()
    else:
        raise Exception(f"User '{username}' already exists (ID: {user.id})")

@user_cli.command("delete")
@click.option("--username", "selector", help="Delete by username.", flag_value="username", default=True)
@click.option("--id", "selector", help="Delete by ID.", flag_value="ID", default=True)
@click.argument("usersel")
@click.option('--yes', is_flag=True, expose_value=False, prompt=f"Are you sure you want to delete this user?")
def delete_user(selector, usersel):
    if selector == "username":
        user = User.query.filter_by(username=usersel).first()
    elif selector == "ID":
        user = User.query.filter_by(id=usersel).first()

    if not user:
        raise KeyError(f"User ({selector} {usersel}) does not exist.")
    else:
        db.session.delete(user)
        db.session.commit()


app.cli.add_command(user_cli)
