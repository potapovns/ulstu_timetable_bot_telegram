import os
import env
from loguru import logger as log
import requests

try:
    import credentials
except ImportError:
    log.warning("Credentials file not found! Please set credentials environ manually.")

API_TIMETABLE_HOST = os.getenv("API_TIMETABLE_HOST")
URL_API = "http://" + API_TIMETABLE_HOST + "/api/timetable"

API_TIMETABLE_SECRET_KEY = os.getenv("API_TIMETABLE_SECRET_KEY")


def extract_dict_weeks_from_json(response_json):
    weeks = response_json['response']['weeks']
    for key, value in weeks.items():
        weeks[int(key) + 1] = value
    return weeks


def get_groups_names_dict():
    response = requests.get(URL_API + "/groups", headers={"auth": API_TIMETABLE_SECRET_KEY})
    response_json = response.json()
    groups = response_json['response']
    groups_dict = {}
    for db_group_name in groups:
        splitted_groups = db_group_name.split(', ')
        for user_group_name in splitted_groups:
            groups_dict[user_group_name] = db_group_name
    return groups_dict
