from os import environ, path
import yaml

config_locations = ["/etc/sachet", "."]
config_path = ""

for dir in config_locations:
    file_path = f"{dir}/config.yml"
    if path.exists(file_path):
        config_path = file_path
        break

if config_path == "":
    raise FileNotFoundError("Please create a configuration: copy config.yml.example to config.yml.")

config = yaml.safe_load(open(config_path))

if config["secret_key"] == "":
    raise ValueError("Please set secret_key within the configuration.")

class BaseConfig:
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = config["sqlalchemy_basedir"] + config["sqlalchemy_basename"] + ".db"
    SECRET_KEY = config["secret_key"]
    BCRYPT_LOG_ROUNDS = config.get("bcrypt_log_rounds", 13)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = config["sqlalchemy_basedir"] + config["sqlalchemy_basename"] + "_test" + ".db"
    BCRYPT_LOG_ROUNDS = config.get("bcrypt_log_rounds", 4)

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = config["sqlalchemy_basedir"] + config["sqlalchemy_basename"] + "_dev" + ".db"
    BCRYPT_LOG_ROUNDS = config.get("bcrypt_log_rounds", 4)

class ProductionConfig(BaseConfig):
    DEBUG = False
