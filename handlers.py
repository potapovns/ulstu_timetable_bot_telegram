import datetime
import os.path
from enum import Enum

import env
import credentials
from keyboards import *

from telegram import Update
from telegram.ext import ContextTypes

from user_states import UserStates
from timetable_themes import TimetableThemes

from functions.db_processing import *

from functions import (
    configuration,
    database,
    logger,
    roles,
    sub
)

CURRENT_WEEK = 0
NEXT_WEEK = 1


def new_message_log(func):
    async def decorated_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
        api_user_id = update.message.from_user.id
        api_user_message = update.message.text.strip()
        log.info(f"New message from user [{api_user_id}]: [{api_user_message}]")
        return await func(update, context)

    return decorated_func


def function_log(func):
    func_name = func.__name__

    async def decorated_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
        nonlocal func_name
        api_user_id = update.message.from_user.id
        api_user_message = update.message.text.strip()
        log.debug(f"[{func_name}] [{api_user_id}] [{api_user_message}]")
        return await func(update, context)

    return decorated_func


def db_user_exist_required(func):
    async def decorated_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_sess = database.db_session.create_session()
        api_user_id = update.message.from_user.id
        db_user = await get_db_user(api_user_id, db_sess)
        db_sess.close()
        if db_user is None:
            log.warning(f"DB User exist required!")
            return await process_message(update, context)
        else:
            return await func(update, context)

    return decorated_func


def db_user_set_group_required(func):
    async def decorated_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_sess = database.db_session.create_session()
        api_user_id = update.message.from_user.id
        db_user = await get_db_user(api_user_id, db_sess)
        db_sess.close()
        if db_user.group is None:
            log.warning(f"DB User set group required!")
            return await please_set_group(update, context)
        else:
            return await func(update, context)

    return decorated_func


@new_message_log
@function_log
async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    api_user = update.message.from_user
    api_user_message = update.message.text.strip()
    api_user_id = api_user.id
    db_sess = database.db_session.create_session()
    db_user = await get_db_user(api_user_id, db_sess)
    if db_user is None:
        db_user = User()
        db_user.api_id = api_user_id
        db_user.theme = TimetableThemes.AUTO
        db_user.group = None
        db_user.group_id = None
        db_user.state = UserStates.PAGE_CONFIGURE

        db_sess.add(db_user)

        db_sess.commit()

        log.info(f"DB added {db_user}")
        await update.message.reply_text(
            "Привет! Я бот, который умеет отсылать расписание УлГТУ :)\n"
            "Чтобы начать получать расписание, укажи свою группу в настройках\n"
            "Также у нас доступна темная тема, нажми \"Сменить тему\", чтобы перейти на темную сторону силы!",
        )
        await command_page_configuration(update, context)
        db_sess.close()
        return

    if db_user.state == UserStates.SET_GROUP:
        group_name = api_user_message
        db_group = await get_db_group(group_name, db_sess)
        if db_group is None:
            await update.message.reply_text(f"Группа \"{group_name}\" не найдена")
            await command_set_group(update, context)
        else:
            await set_db_user_group(db_user, db_sess, db_group)
            await update.message.reply_text(f"Группа изменена на {db_group.name}")
            await set_db_user_state(db_user, db_sess, UserStates.PAGE_TIMETABLE)
            await command_page_timetable(update, context)
        db_sess.close()
        return

    elif db_user.state == UserStates.SET_THEME:
        if api_user_message not in TimetableThemes.THEMES.keys():
            await update.message.reply_text("Такой темы еще нет)\nНо все еще впереди...")
            await command_page_configuration(update, context)
            db_sess.close()
            return
        db_user.theme = TimetableThemes.THEMES[api_user_message]
        db_sess.commit()
        log.debug(f"DB updated theme {db_user}")
        await set_db_user_state(db_user, db_sess, UserStates.PAGE_TIMETABLE)
        await update.message.reply_text(f"Тема изменена на \"{api_user_message}\"")
        await command_page_timetable(update, context)
        db_sess.close()
        return
    elif db_user.state == UserStates.PAGE_CONFIGURE:
        await command_page_configuration(update, context)
        db_sess.close()
        return
    elif db_user.state == UserStates.PAGE_TIMETABLE:
        await command_page_timetable(update, context)
        db_sess.close()
        return
    await command_page_timetable(update, context)
    db_sess.close()
    return


@new_message_log
@db_user_exist_required
@function_log
async def command_page_timetable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    api_user_id = update.message.from_user.id
    db_sess = database.db_session.create_session()
    db_user = await get_db_user(api_user_id, db_sess)
    await set_db_user_state(db_user, db_sess, UserStates.PAGE_TIMETABLE)
    db_sess.close()
    await update.message.reply_text("Расписание", reply_markup=KEYBOARD_TIMETABLE_MARKUP)


@new_message_log
@db_user_exist_required
@function_log
async def command_page_configuration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    api_user_id = update.message.from_user.id
    db_sess = database.db_session.create_session()
    db_user = await get_db_user(api_user_id, db_sess)
    await set_db_user_state(db_user, db_sess, UserStates.PAGE_CONFIGURE)
    db_sess.close()
    await update.message.reply_text("Настройки", reply_markup=KEYBOARD_CONFIGURE_MARKUP)


@new_message_log
@db_user_exist_required
@db_user_set_group_required
@function_log
async def command_get_current_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await try_get_week(update, context, CURRENT_WEEK)


@new_message_log
@db_user_exist_required
@db_user_set_group_required
@function_log
async def command_get_next_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await try_get_week(update, context, NEXT_WEEK)


@new_message_log
@db_user_exist_required
@function_log
async def command_set_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    api_user_id = update.message.from_user.id
    db_sess = database.db_session.create_session()
    db_user = await get_db_user(api_user_id, db_sess)
    await set_db_user_state(db_user, db_sess, UserStates.SET_THEME)
    db_sess.close()
    await update.message.reply_text("Выберите тему:", reply_markup=KEYBOARD_THEME_MARKUP)


@new_message_log
@db_user_exist_required
@function_log
async def command_set_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    api_user_id = update.message.from_user.id
    db_sess = database.db_session.create_session()
    db_user = await get_db_user(api_user_id, db_sess)
    await set_db_user_state(db_user, db_sess, UserStates.SET_GROUP)
    db_sess.close()
    await update.message.reply_text("Напишите название группы:", reply_markup=KEYBOARD_BACK_MARKUP)


@new_message_log
@db_user_exist_required
@function_log
async def command_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await command_page_configuration(update, context)


@function_log
async def please_set_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Чтобы получить расписание, укажите свою группу в настройках")


async def try_get_week(update: Update, context: ContextTypes.DEFAULT_TYPE, week) -> None:
    api_user_id = update.message.from_user.id
    db_sess = database.db_session.create_session()
    db_user = await get_db_user(api_user_id, db_sess)
    current_week_number = sub.get_current_week_number()
    target_week_number = current_week_number + week
    db_image, is_actual = await sub.try_get_group_timetable_image_for_week(
        db_sess, db_user, target_week_number, current_week=True if week == CURRENT_WEEK else False
    )
    config = configuration.get_configuration_from_file(
        configuration.get_config_filename()
    )
    # Выдать расписание
    if db_image is None:
        await update.message.reply_text("К сожалению, расписание временно недоступно :(\n"
                                        "Пожалуйста, повторите попытку позже...")
    else:
        db_image_path = os.path.join(
            os.getcwd(),
            config["images_config"]["folder"],
            db_image.filename
        )
        if not os.path.exists(db_image_path):
            db_sess.delete(db_image)
            db_sess.commit()
            db_image, is_actual = await sub.try_get_group_timetable_image_for_week(
                db_sess, db_user, target_week_number,
                current_week=True if week == CURRENT_WEEK else False
            )
            if db_image is None:
                await update.message.reply_text("К сожалению, расписание временно недоступно :(\n"
                                                "Пожалуйста, повторите попытку позже...")
                db_sess.close()
                return
        if week == CURRENT_WEEK:
            week_text = "Текущая неделя"
        elif week == NEXT_WEEK:
            week_text = "Следующая неделя"
        reply_message_text = f"Расписание для группы {db_user.group.name}\n" \
                             f"{week_text} {target_week_number}"
        if is_actual:
            await update.message.reply_text(reply_message_text)
        else:
            actual_time = db_image.timetable.updated_datetime.strftime("%H:%M %m.%d.%Y")
            reply_message_text = f"По состоянию на {actual_time}\n" + reply_message_text
            await update.message.reply_text(reply_message_text)
        await update.message.reply_photo(
            photo=open(db_image_path, 'rb')
        )
    db_sess.close()
