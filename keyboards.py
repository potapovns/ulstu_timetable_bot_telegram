from telegram import KeyboardButton, ReplyKeyboardMarkup

KEYBOARD_TIMETABLE_MARKUP = ReplyKeyboardMarkup([
    [
        KeyboardButton("Текущая неделя"),
        KeyboardButton("Следующая неделя")
    ],
    [
        KeyboardButton("Настройки")
    ]
], resize_keyboard=True)

KEYBOARD_CONFIGURE_MARKUP = ReplyKeyboardMarkup([
    [
        KeyboardButton("Расписание")
    ],
    [
        KeyboardButton("Сменить группу")
    ],
    [
        KeyboardButton("Сменить тему")
    ]
], resize_keyboard=True)

KEYBOARD_THEME_MARKUP = ReplyKeyboardMarkup([
    [
        KeyboardButton("Светлая"),
        KeyboardButton("Авто"),
        KeyboardButton("Темная")
    ],
    [
        KeyboardButton("Назад")
    ]
], resize_keyboard=True)

KEYBOARD_BACK_MARKUP = ReplyKeyboardMarkup([
    [
        KeyboardButton("Назад")
    ]
], resize_keyboard=True)
