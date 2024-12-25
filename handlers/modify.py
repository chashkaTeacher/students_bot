import re
from core import *
from main import handle_confirmation, handle_delete_description


# Обработка выбора поля
async def handle_edit_field(update: Update, context: CallbackContext):
    query = update.callback_query
    field = query.data.split(":")[1]  # Извлекаем поле для изменения
    context.user_data['editing_field'] = field  # Сохраняем редактируемое поле
    context.user_data['state'] = "UPDATING_FIELD"  # Устанавливаем состояние

    if field == "exam":
        # Показываем reply-кнопки для выбора экзамена
        reply_markup = ReplyKeyboardMarkup(
            [['ОГЭ', 'ЕГЭ']],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await query.message.reply_text("Выберите новый экзамен:", reply_markup=reply_markup)
        return  # Завершаем выполнение, чтобы не запрашивать текстовый ввод

    # Если редактируемое поле — описание
    if field == "description":
        # Сообщение с текущим описанием и кнопкой "Удалить описание"
        message_text = f"Введите новое описание или нажмите кнопку 'Удалить описание'."
        reply_markup = ReplyKeyboardMarkup(
            [['Удалить описание']],
            one_time_keyboard=True,
            resize_keyboard=True
        )

        await query.message.reply_text(message_text, reply_markup=reply_markup)
        return  # Завершаем выполнение

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
    state = user_data.get('state')  # Получаем текущее состояние пользователя
    editing_field = user_data.get('editing_field')

    # Если пользователь нажимает "Удалить описание"
    if editing_field == "description" and update.message.text == "Удалить описание":
        await handle_delete_description(update, context)
        return

    if not state:
        await update.message.reply_text("Напишите /start, чтобы начать.")
        return

    if state == "CHOOSING_FIELD":
        await handle_edit_field(update, context)

    elif state == "UPDATING_FIELD":
        await handle_new_value(update, context)

    elif state == "CONFIRMATION":
        await handle_confirmation(update, context)

    else:
        return


async def handle_new_value(update: Update, context: CallbackContext):
    new_value = update.message.text
    field = context.user_data.get('editing_field')

    # Проверка на пустую строку для описания
    if field == "description" and new_value.strip() == "":
        new_value = None  # Устанавливаем None для базы данных, если строка пустая

    # Проверка на корректность ссылки
    if field == "class_link":
        if not re.match(r"^https?://", new_value):
            await update.message.reply_text("Пожалуйста, введите корректную ссылку (начинается с http:// или https://)")
            return  # Оставляем состояние UPDATING_FIELD для повторного ввода

    # Сохраняем новое значение и состояние
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
