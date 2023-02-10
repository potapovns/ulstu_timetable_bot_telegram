import os
import sys
import datetime
from loguru import logger


class Rotator:
    """
    Класс-ротатор для файлов логов
    """

    def __init__(self):
        self._last_date = datetime.date.today()

    def should_rotate(self, message, file):
        current_date = datetime.date.today()
        if current_date != self._last_date:
            self._last_date = datetime.date.today()
            return True
        return False


def get_log_files_path(log_filename):
    log_folder = os.getenv("LOG_FOLDER")
    log_path = os.path.join(os.getcwd(), log_folder, log_filename)
    return log_path


def initialize_logger():
    log_filename_template = "log_{time:DD-MM-YYYY}.log"
    log_path = get_log_files_path(log_filename_template)
    rotator = Rotator()
    logger.remove(0)
    log_format = "<level>{level}</level>\t|\t{time:DD-MM-YYYY HH:mm:ss.SSS}\t|\t{elapsed}\t|\t{file}\t|\t{message}"
    logger.add(
        sys.stdout,
        format=log_format,
        colorize=True
    )
    logger.add(
        log_path,
        format=log_format,
        rotation=rotator.should_rotate
    )
