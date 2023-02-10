import os

from .configuration import (
    get_config_filename,
    get_configuration_from_file
)
from data import db_session


def get_database_connection_config(configuration, database_username, database_password):
    db_config = configuration["database_config"]
    db_config["username"] = database_username
    db_config["password"] = database_password
    return db_config


def get_database_credentials():
    username = os.getenv("DATABASE_USERNAME")
    password = os.getenv("DATABASE_PASSWORD")
    return username, password


def initialize_database_session():
    config_filename = get_config_filename()
    db_config = get_configuration_from_file(config_filename)
    db_username, db_password = get_database_credentials()
    db_connection_config = get_database_connection_config(
        db_config,
        db_username,
        db_password
    )
    db_session.global_init(db_connection_config)
