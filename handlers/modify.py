import re
from core import *
from main import handle_confirmation


# Обработка выбора поля
async def handle_edit_field(update: Update, context: CallbackContext):
    query = update.callback_query
    field = query.data.split(":")[1]
    context.user_data['editing_field'] = field
    context.user_data['state'] = "UPDATING_FIELD"  # Устанавливаем состояние

    if field == "exam":
        reply_markup = ReplyKeyboardMarkup([['ОГЭ', 'ЕГЭ']], one_time_keyboard=True, resize_keyboard=True)
        await query.message.reply_text("Выберите новый экзамен:", reply_markup=reply_markup)
        return

    if field == "description":
        reply_markup = ReplyKeyboardMarkup([['Удалить описание']], one_time_keyboard=True, resize_keyboard=True)
        await query.message.reply_text("Введите новое описание или нажмите кнопку 'Удалить описание':",
                                       reply_markup=reply_markup)
        return

    field_name = {
        "name": "имя",
        "class_date": "дату занятия",
        "class_link": "ссылку на занятие",
        "description": "описание"
    }.get(field, "значение")

    await query.edit_message_text(f"Введите новое {field_name}:")


async def handle_new_exam(update: Update, context: CallbackContext):
    query = update.callback_query
    new_exam = query.data.split(":")[1]  # Извлекаем выбранный экзамен
    context.user_data['new_value'] = new_exam
    context.user_data['editing_field'] = "exam"
    context.user_data['state'] = "CONFIRMATION"  # Устанавливаем состояние подтверждения

    await query.answer("Выбран новый экзамен.")
    await query.edit_message_text(f"Вы выбрали {new_exam}. Подтвердить изменения?")


async def global_message_handler(update: Update, context: CallbackContext):
    user_data = context.user_data
    state = user_data.get('state')

    if not state:
        await update.message.reply_text("Напишите /start, чтобы начать.")
        return

    if state == "UPDATING_FIELD":
        await handle_new_value(update, context)
    elif state == "CONFIRMATION":
        await handle_confirmation(update, context)
    else:
        await update.message.reply_text("Неизвестное состояние. Попробуйте снова.")


async def handle_new_value(update: Update, context: CallbackContext):
    new_value = update.message.text
    field = context.user_data.get('editing_field')

    if field == "description" and new_value.strip() == "":
        new_value = None

    if field == "class_link" and not re.match(r"^https?://", new_value):
        await update.message.reply_text("Пожалуйста, введите корректную ссылку (начинается с http:// или https://)")
        return

    context.user_data['new_value'] = new_value
    context.user_data['state'] = "CONFIRMATION"  # Устанавливаем состояние подтверждения

    field_name = {
        "name": "имя",
        "class_date": "дату занятия",
        "class_link": "ссылку на занятие",
        "description": "описание"
    }.get(field, "значение")

    markup = ReplyKeyboardMarkup([['Да', 'Нет']], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        f"Вы ввели новое {field_name}: {new_value if new_value is not None else 'пустая строка'}. "
        f"Подтвердить изменения?",
        reply_markup=markup
    )
