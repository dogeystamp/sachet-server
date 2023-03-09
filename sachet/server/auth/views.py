from flask import Blueprint

auth_blueprint = Blueprint("auth_blueprint", __name__)

@auth_blueprint.route('/')
def index():
    return "Hello world"
