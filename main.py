import os
import sys

import env
import functions.my_api
import handlers
import credentials
from keyboards import *

from data.users import User
from data.groups import Group
from data.timetables import Timetable
from data.images import Image

from functions import (
    configuration,
    database,
    logger,
    roles
)
from telegram.ext import (
    Application,
    MessageHandler,
    filters
)
from loguru import logger as log

TOKEN = os.getenv("TELEGRAM_TOKEN")


def db_groups_add_new(groups_dict):
    db_sess = database.db_session.create_session()
    db_groups_all = db_sess.query(Group).all()
    db_groups_all_names = [db_group.name for db_group in db_groups_all]
    for user_group_name, db_group_name in groups_dict.items():
        if db_group_name not in db_groups_all_names:
            new_group = Group()
            new_group.name = db_group_name
            db_sess.add(new_group)
            log.debug(f"New group added: {new_group}")
    db_sess.commit()


def main():
    logger.initialize_logger()
    log.info("Logger initialized")

    database.initialize_database_session()
    log.info("Database session initialized")

    groups_dict = functions.my_api.get_groups_names_dict()
    db_groups_add_new(groups_dict)
    log.info("Groups list updated")

    application = Application.builder().token(TOKEN).build()
    log.info("Telegram connection initialized")

    application.add_handler(
        MessageHandler(filters.Regex("^Назад$"), handlers.command_back))
    application.add_handler(
        MessageHandler(filters.Regex("^Сменить группу$"), handlers.command_set_group))
    application.add_handler(
        MessageHandler(filters.Regex("^Сменить тему"), handlers.command_set_theme))
    application.add_handler(
        MessageHandler(filters.Regex("^Следующая неделя$"), handlers.command_get_next_week))
    application.add_handler(
        MessageHandler(filters.Regex("^Следующая неделя$"), handlers.command_get_next_week))
    application.add_handler(
        MessageHandler(filters.Regex("^Текущая неделя$"), handlers.command_get_current_week))
    application.add_handler(
        MessageHandler(filters.Regex("^Расписание$"), handlers.command_page_timetable))
    application.add_handler(
        MessageHandler(filters.Regex("^Настройки$"), handlers.command_page_configuration))
    application.add_handler(MessageHandler(filters.Regex(".*"), handlers.process_message))
    log.info("Handlers initialized")

    log.info("Polling is running")
    application.run_polling()


if __name__ == '__main__':
    main()
