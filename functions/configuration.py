import os
import env
import json


def get_configuration_from_file(config_filename):
    with open(config_filename) as file:
        config_json = json.load(file)
    return config_json


def get_config_filename():
    config_filename = os.getenv("CONFIG_FILE")
    return config_filename


def get_bells_config_filename():
    config_filename = os.getenv("BELLS_CONFIG_FILE")
    return config_filename
