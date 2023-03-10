import os
import env
import time
import handlers
from loguru import logger as log

try:
    import credentials
except ImportError:
    log.warning("Credentials file not found! Please set credentials environ manually.")

from functions import (
    database,
    logger,
    my_api,
    sub
)

from telegram.ext import (
    Application,
    MessageHandler,
    filters
)

TOKEN = os.getenv("TELEGRAM_TOKEN")


def main():
    try:
        os.environ['TZ'] = 'Europe/Samara'
        time.tzset()
    except Exception as e:
        log.warning("Timezone isn`t set! Please set timezone")

    logger.initialize_logger()
    log.info("Logger initialized")

    database.initialize_database_session()
    log.info("Database session initialized")

    groups_dict = my_api.get_groups_names_dict()
    sub.db_groups_add_new(groups_dict)
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
