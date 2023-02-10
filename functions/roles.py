import os
import json


def get_roles_file_path():
    roles_filename = os.getenv("ROLES_FILE")
    roles_path = os.path.join(os.getcwd(), roles_filename)
    return roles_path


def get_roles_config_from_file(roles_filename):
    with open(roles_filename) as file:
        roles_json = json.load(file)
    return roles_json


def get_admins_ids_from_config(roles_configuration=None):
    if roles_configuration is not None:
        return roles_configuration["admin"]
    config_path = get_roles_file_path()
    config = get_roles_config_from_file(config_path)
    admins_ids = get_admins_ids_from_config(config)
    return admins_ids


def get_roles_configuration():
    roles_filename = get_roles_file_path()
    roles_config = get_roles_config_from_file(roles_filename)
    return roles_config
