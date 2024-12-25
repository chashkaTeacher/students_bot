# Токен бота
BOT_TOKEN = ""

# IDs администраторов
ADMIN_IDS = []

HOMEWORK_OPTIONS = {
    "ЕГЭ": {
        "Задание 1": "...",

    },
    "ОГЭ": {
        "Задание 1": "...",

    }
}

NOTES_OPTIONS = {
    "ЕГЭ": {
        "Задание 1": "...",

    },
    "ОГЭ": {
        "Конспект 1": "...",
    }
}

CHOOSING, TYPING_NAME, TYPING_EXAM, DELETING, STUDENT_LOGIN, STUDENT_MENU, ADD_VARIANT, ADD_VARIANT_LINK, \
 TYPING_CLASS_LINK, TYPING_CLASS_DATE, CHOOSING_FIELD, UPDATING_FIELD, CONFIRMATION= range(13)

# Добавляем всё в __all__
__all__ = [
    "BOT_TOKEN",
    "ADMIN_IDS",
    "HOMEWORK_OPTIONS",
    "NOTES_OPTIONS",
    "CHOOSING", "TYPING_NAME", "TYPING_EXAM", "DELETING", "STUDENT_LOGIN", "STUDENT_MENU",
    "ADD_VARIANT", "ADD_VARIANT_LINK", "TYPING_CLASS_LINK", "TYPING_CLASS_DATE",
    "CHOOSING_FIELD", "UPDATING_FIELD", "CONFIRMATION"
]
