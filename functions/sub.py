import os
import datetime

import timetable_themes
from data.groups import Group
from data.images import Image
from data.timetables import Timetable
from data.users import User
from functions import configuration, my_api

from loguru import logger as log

import TimetableToImage


def get_week_number(first_week_start_date, target_date: datetime.date):
    current_week_num = (target_date - first_week_start_date).days // 7 + 1
    return current_week_num


def get_current_week_number():
    config = configuration.get_configuration_from_file(
        configuration.get_config_filename()
    )
    now_date = datetime.date.today()
    semester_start_date = get_current_semester_start_date(
        config["semesters_config"],
        now_date
    )
    current_week_number = get_week_number(semester_start_date, now_date)
    return current_week_number


def get_week_period_by_week_number(first_week_start_date, week_number):
    target_week_first_day = first_week_start_date + datetime.timedelta(days=((week_number - 1) * 7))
    target_week_last_day = target_week_first_day + datetime.timedelta(days=6)
    return target_week_first_day, target_week_last_day


def get_current_semester_start_date(semester_config, target_date: datetime.date):
    if target_date.month < 8:
        first_date = semester_config["spring"]["start_date"]
    else:
        first_date = semester_config["autumn"]["start_date"]
    first_date_split = [int(x) for x in first_date.split('.')]
    return datetime.date(*first_date_split[::-1])


def get_actual_period_from_config(config: dict) -> datetime.timedelta:
    str_actual_period: str = config["timetables_config"]["actual_period"]
    split_actual_period = list(map(int, str_actual_period.split(':')))
    actual_period = datetime.timedelta(
        hours=split_actual_period[0],
        minutes=split_actual_period[1],
        seconds=split_actual_period[2]
    )
    return actual_period


def get_time_from_str(str_time: str) -> datetime.time:
    split_time = str_time.split(':')
    int_time = [int(x) for x in split_time]
    return datetime.time(hour=int_time[0], minute=int_time[1], second=int_time[2])


def get_current_timetable_theme():
    config = configuration.get_configuration_from_file(
        configuration.get_config_filename()
    )
    auto_dark_theme_config = config["auto_dark_theme_config"]
    begin = get_time_from_str(auto_dark_theme_config["begin"])
    end = get_time_from_str(auto_dark_theme_config["end"])
    if end > begin:
        if begin <= datetime.datetime.now().time() <= end:
            return timetable_themes.TimetableThemes.DARK
    else:
        if begin <= datetime.datetime.now().time() or datetime.datetime.now().time() < end:
            return timetable_themes.TimetableThemes.DARK
    return timetable_themes.TimetableThemes.LIGHT


async def drop_timetable_cascade(db_sess, db_timetable: Timetable) -> None:
    db_sess.delete(db_timetable)
    db_sess.commit()


async def try_get_group_timetable_image_for_week(db_sess, db_user: User, week_number: int,
                                                 current_week=False):
    db_group: Group = db_user.group
    db_timetables = db_group.timetables
    db_timetable = None
    deleted = None
    for timetable in db_timetables:
        timetable: Timetable
        if current_week:
            if timetable.week_number == week_number - 1:
                deleted = timetable
        if timetable.week_number == week_number:
            db_timetable = timetable
    if current_week and deleted is not None:
        await drop_timetable_cascade(db_sess, deleted)
    timetable_is_actual = False
    if db_timetable is None:
        group_weeks_json = None
        try:
            group_weeks_json = await my_api.get_group_timetable(db_group.name)
        except Exception as e:
            log.exception("")
        if group_weeks_json is None:
            return None, timetable_is_actual
        if week_number not in group_weeks_json:
            return None, timetable_is_actual
        db_timetable = Timetable()
        db_timetable.group = db_group
        db_timetable.week_number = week_number
        db_timetable.week_json = group_weeks_json[week_number]
        db_timetable.updated_datetime = datetime.datetime.now()
        db_sess.add(db_timetable)
        db_sess.commit()
    config = configuration.get_configuration_from_file(
        configuration.get_config_filename()
    )
    config_actual_period = get_actual_period_from_config(config)
    if datetime.datetime.now() - db_timetable.updated_datetime < config_actual_period:
        timetable_is_actual = True
    if not timetable_is_actual:
        group_weeks_json = None
        try:
            group_weeks_json = await my_api.get_group_timetable(db_group.name)
        except Exception as e:
            log.exception("")
        if group_weeks_json is not None:
            if week_number in group_weeks_json:
                db_timetable.week_json = group_weeks_json[week_number]
                db_timetable.updated_datetime = datetime.datetime.now()
                for image in db_timetable.images:
                    db_sess.delete(image)
                db_sess.commit()
                timetable_is_actual = True
    db_images = db_timetable.images
    user_theme = db_user.theme
    if user_theme is None or user_theme == timetable_themes.TimetableThemes.AUTO:
        target_theme = get_current_timetable_theme()
    else:
        target_theme = user_theme
    db_image = None
    for image in db_images:
        image: Image
        if image.theme == target_theme:
            db_image = image
            break
    if db_image is None:
        week_begin, week_end = get_week_period_by_week_number(
            get_current_semester_start_date(
                config["semesters_config"],
                datetime.date.today()
            ),
            week_number
        )
        tw = TimetableToImage.Timetable.get_timetable_week_from_json(
            db_timetable.week_json,
            week_begin=week_begin,
            week_end=week_end
        )
        tw.group = db_group.name
        tw.number = week_number
        bells_config = configuration.get_configuration_from_file(
            configuration.get_bells_config_filename()
        )
        tb = TimetableToImage.Timetable.get_timetable_bells_from_json(
            bells_config["default"]
        )
        img = TimetableToImage.Image.generate_from_timetable_week(
            tw,
            tb,
            inverted=True if target_theme == timetable_themes.TimetableThemes.DARK else False,
            text_promotion=config["promotion_config"]["telegram_bot_link"]
        )
        week_text = "CURRENT" if current_week else "NEXT"
        img_filename = f"timetable_{db_group.name}_{week_text}_{target_theme}.png"
        img_folder_path = os.path.join(
            os.getcwd(),
            config["images_config"]["folder"]
        )
        if not os.path.exists(img_folder_path):
            os.mkdir(img_folder_path)
        img_path = os.path.join(
            os.getcwd(),
            config["images_config"]["folder"],
            img_filename
        )
        img.save(
            img_path,
            "PNG"
        )
        db_image = Image()
        db_image.timetable = db_timetable
        db_image.filename = img_filename
        db_image.theme = target_theme
        db_sess.add(db_image)
        db_sess.commit()

    return db_image, timetable_is_actual
