from os import getenv, path
import yaml

sqlalchemy_base = "sqlite:///sachet"


class BaseConfig:
    SQLALCHEMY_DATABASE_URI = sqlalchemy_base + ".db"
    BCRYPT_LOG_ROUNDS = 13
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestingConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = sqlalchemy_base + "_test" + ".db"
    BCRYPT_LOG_ROUNDS = 4


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = sqlalchemy_base + "_dev" + ".db"
    BCRYPT_LOG_ROUNDS = 4


class ProductionConfig(BaseConfig):
    pass


def overlay_config(base, config_file=None):
    """Reading from a YAML file, this overrides configuration options from the bases above."""
    config_locations = [config_file, "/etc/sachet/config.yml", "./config.yml"]

    config_path = ""

    for loc in config_locations:
        if not loc:
            continue
        if path.exists(loc):
            config_path = loc
            break

    if config_path == "":
        raise FileNotFoundError(
            "Please create a configuration: copy config.yml.example to config.yml."
        )

    config = yaml.safe_load(open(config_path))

    if config["SECRET_KEY"] == "" or config["SECRET_KEY"] is None:
        raise ValueError("Please set secret_key within the configuration.")

    from sachet.server import app

    app.config.from_object(base)

    for k, v in config.items():
        app.config[k] = v
