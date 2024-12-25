from core import *
from database import *


# Меню ученика
async def student_menu(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardMarkup(
        [
            ['Домашнее задание', 'Актуальный вариант'],  # Первая строка
            ['Конспекты', 'Подключиться к занятию'],  # Вторая строка
            ['Вернуться в главное меню']  # Третья строка
        ],
        resize_keyboard=True
    )
    if update.message:
        await update.message.reply_text("Вы в меню ученика:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer("Возврат в меню.")
        await update.callback_query.edit_message_text("Вы в меню ученика:")
    return STUDENT_MENU

# Обработка входа ученика
async def student_login(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id  # Получаем Telegram ID
    password = update.message.text  # Получаем пароль

    # Проверяем, зарегистрирован ли ученик по Telegram ID
    user = get_user_by_telegram_id(telegram_id)
    if user:
        user_id, name, exam = user
        await update.message.reply_text(f"Добро пожаловать, {name}!")
        return await student_menu(update, context)

    # Проверяем пароль
    user = get_user_by_password(password)
    if user:
        user_id, name, exam = user
        # Обновляем Telegram ID
        update_user_telegram_id(user_id, telegram_id)
        await update.message.reply_text(
            f"Добро пожаловать, {name}!\nВаш Telegram ID сохранен для автоматических входов."
        )
        return await student_menu(update, context)

    # Если ни Telegram ID, ни пароль не подходят
    await update.message.reply_text("Неверный пароль. Попробуйте снова.")
    return STUDENT_LOGIN


async def return_to_student_menu(update: Update, context: CallbackContext):
    """Возврат в меню ученика."""
    await update.callback_query.answer("Возврат в меню.")
    await update.callback_query.edit_message_text("Вы вернулись в меню.")
    return STUDENT_MENU


# Обработка выбора в меню ученика
async def handle_student_menu(update: Update, context: CallbackContext):
    choice = update.message.text
    telegram_id = update.message.from_user.id

    if choice == "Домашнее задание":
        # Получаем задание ученика
        with sqlite3.connect('your_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT homework, class_date FROM users WHERE telegram_id = ?', (telegram_id,))
            homework_link = cursor.fetchone()

        if homework_link and homework_link[0]:
            link, class_date = homework_link
            keyboard = [
                [InlineKeyboardButton("Открыть домашнее задание", url=homework_link[0])],
                [InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Дата занятия: {class_date}\n\n"
                f"Вот ваше домашнее задание. Нажмите на кнопку ниже, чтобы открыть его:",
                reply_markup=reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("У вас пока нет заданий.", reply_markup=reply_markup)
        return STUDENT_MENU

    elif choice == "Конспекты":
        # Получаем экзамен ученика
        with sqlite3.connect('your_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT exam FROM users WHERE telegram_id = ?', (telegram_id,))
            exam = cursor.fetchone()

        if not exam:
            keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Ошибка: экзамен не найден.", reply_markup=reply_markup)
            return STUDENT_MENU

        exam = exam[0]  # Извлекаем название экзамена (ОГЭ или ЕГЭ)

        # Формируем кнопки для конспектов по экзамену (по 2 в ряду)
        notes = NOTES_OPTIONS.get(exam, {})
        keyboard = []
        row = []
        for idx, (name, link) in enumerate(notes.items(), start=1):
            row.append(InlineKeyboardButton(name, url=link))
            if len(row) == 2 or idx == len(notes):  # Завершаем строку после двух кнопок или в конце
                keyboard.append(row)
                row = []
        keyboard.append([InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")])  # Кнопка возврата

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Выберите конспект:", reply_markup=reply_markup)
        return STUDENT_MENU

    elif choice == "Актуальный вариант":
        return await show_variant(update, context)

    elif choice == "Подключиться к занятию":
        # Получаем ссылку на занятие ученика
        with sqlite3.connect('your_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT class_link FROM users WHERE telegram_id = ?', (telegram_id,))
            class_link = cursor.fetchone()

        if class_link and class_link[0]:
            keyboard = [
                [InlineKeyboardButton("Подключиться", url=class_link[0])],
                [InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Вот ссылка для подключения к занятию:", reply_markup=reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Ссылка на занятие пока недоступна.", reply_markup=reply_markup)
        return STUDENT_MENU

    else:
        keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите действие из меню.", reply_markup=reply_markup)
        return STUDENT_MENU


# Функция для отображения варианта ученику
async def show_variant(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id

    # Получаем экзамен и актуальный вариант для ученика
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT exam FROM users WHERE telegram_id = ?', (telegram_id,))
        exam = cursor.fetchone()

    if not exam:
        keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Ошибка: экзамен не найден.", reply_markup=reply_markup)
        return STUDENT_MENU

    exam = exam[0]  # Извлекаем название экзамена (ОГЭ или ЕГЭ)

    # Получаем ссылку на актуальный вариант
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT link FROM variants WHERE exam = ?', (exam,))
        variant = cursor.fetchone()

    if variant and variant[0]:
        keyboard = [
            [InlineKeyboardButton("Открыть вариант", url=variant[0])],
            [InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Вот ваш актуальный вариант экзамена:", reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Актуальный вариант пока недоступен.", reply_markup=reply_markup)

    return STUDENT_MENU



async def show_class_link(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id

    # Извлекаем ссылку на занятие для ученика
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT class_link FROM users WHERE telegram_id = ?', (telegram_id,))
        class_link = cursor.fetchone()

    if not class_link or not class_link[0]:
        await update.message.reply_text("Ссылка для подключения к занятию не найдена.")
    else:
        # Создаем inline-кнопку ссылкой
        keyboard = [[InlineKeyboardButton("Перейти к занятию", url=class_link[0])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Нажмите на кнопку ниже, чтобы подключиться к занятию:",
                                        reply_markup=reply_markup)

    return STUDENT_MENU


async def handle_show_student_info(update: Update, context: CallbackContext):
    query = update.callback_query
    student_id = int(query.data.split(":")[1])  # Извлекаем ID ученика из callback_data

    # Получаем данные об ученике
    student_info = get_student_info(student_id)
    if not student_info:
        await query.answer("Ошибка: ученик не найден.")
        return

    # Формируем сообщение с информацией об ученике
    message_text = (
            f"📋 Информация об ученике:\n"
            f"👤 Имя: {student_info['name']}\n"
            f"📚 Экзамен: {student_info['exam']}\n"
            f"📅 Дата занятия: {student_info['class_date']}\n"
            f"🔗 Ссылка на занятие: {student_info['class_link']}\n"
            f"📝 Описание: {student_info['description']}\n"
            f"📄 Домашнее задание: {student_info['homework']}\n"
            f"🆔 Telegram ID: {student_info['telegram_id']}\n"
            f"🔑 Пароль: {student_info['password']}"
        )

    # Добавляем кнопку "Вернуться в меню"
    keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text(message_text, reply_markup=reply_markup)

