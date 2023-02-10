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
    roles
)


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
        return

    if db_user.state == UserStates.SET_GROUP:
        group_name = api_user_message
        db_group = await get_db_group(group_name, db_sess)
        if db_group is None:
            await update.message.reply_text(f"Группа \"{group_name}\" не найдена")
            await command_set_group(update, context)
        else:
            await set_db_user_group(db_user, db_sess, db_group)
            await update.message.reply_text(f"Группа изменена на {group_name}")
            await set_db_user_state(db_user, db_sess, UserStates.PAGE_TIMETABLE)
            await command_page_timetable(update, context)

    elif db_user.state == UserStates.SET_THEME:
        if api_user_message not in TimetableThemes.THEMES.keys():
            await update.message.reply_text("Такой темы еще нет)\nНо все еще впереди...")
            await command_page_configuration(update, context)
            return
        db_user.theme = TimetableThemes.THEMES[api_user_message]
        db_sess.commit()
        log.debug(f"DB updated theme {db_user}")
        await set_db_user_state(db_user, db_sess, UserStates.PAGE_TIMETABLE)
        await update.message.reply_text(f"Тема изменена на \"{api_user_message}\"")
        await command_page_timetable(update, context)
    elif db_user.state == UserStates.PAGE_CONFIGURE:
        await command_page_configuration(update, context)
    elif db_user.state == UserStates.PAGE_TIMETABLE:
        await command_page_timetable(update, context)


@new_message_log
@db_user_exist_required
@function_log
async def command_page_timetable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    api_user_id = update.message.from_user.id
    db_sess = database.db_session.create_session()
    db_user = await get_db_user(api_user_id, db_sess)
    await set_db_user_state(db_user, db_sess, UserStates.PAGE_TIMETABLE)
    await update.message.reply_text("Расписание", reply_markup=KEYBOARD_TIMETABLE_MARKUP)


@new_message_log
@db_user_exist_required
@function_log
async def command_page_configuration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    api_user_id = update.message.from_user.id
    db_sess = database.db_session.create_session()
    db_user = await get_db_user(api_user_id, db_sess)
    await set_db_user_state(db_user, db_sess, UserStates.PAGE_CONFIGURE)
    await update.message.reply_text("Настройки", reply_markup=KEYBOARD_CONFIGURE_MARKUP)


@new_message_log
@db_user_exist_required
@db_user_set_group_required
@function_log
async def command_get_current_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    api_user_id = update.message.from_user.id
    db_sess = database.db_session.create_session()
    db_user = await get_db_user(api_user_id, db_sess)
    # TODO
    # Выдать расписание
    await update.message.reply_text("Расписание для группы...\nТекущая неделя...")


@new_message_log
@db_user_exist_required
@db_user_set_group_required
@function_log
async def command_get_next_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    api_user_id = update.message.from_user.id
    db_sess = database.db_session.create_session()
    db_user = await get_db_user(api_user_id, db_sess)
    # TODO
    # Выдать расписание
    await update.message.reply_text("Расписание для группы...\nСледующая неделя...")


@new_message_log
@db_user_exist_required
@function_log
async def command_set_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    api_user_id = update.message.from_user.id
    db_sess = database.db_session.create_session()
    db_user = await get_db_user(api_user_id, db_sess)
    await set_db_user_state(db_user, db_sess, UserStates.SET_THEME)
    await update.message.reply_text("Выберите тему:", reply_markup=KEYBOARD_THEME_MARKUP)


@new_message_log
@db_user_exist_required
@function_log
async def command_set_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    api_user_id = update.message.from_user.id
    db_sess = database.db_session.create_session()
    db_user = await get_db_user(api_user_id, db_sess)
    await set_db_user_state(db_user, db_sess, UserStates.SET_GROUP)
    await update.message.reply_text("Напишите название группы:", reply_markup=KEYBOARD_BACK_MARKUP)


@new_message_log
@db_user_exist_required
@function_log
async def command_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await command_page_configuration(update, context)


@function_log
async def please_set_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Чтобы получить расписание, укажите свою группу в настройках")
