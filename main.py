import datetime
from database import *
from handlers.modify import *
from handlers.student import student_menu, student_login, handle_student_menu, handle_show_student_info, return_to_student_menu


def create_reply_keyboard(buttons, row_width=2, one_time_keyboard=True, resize_keyboard=True):
    """
    Создает Reply-клавиатуру.

    :param buttons: Список кнопок.
    :param row_width: Количество кнопок в строке (по умолчанию 2).
    :param one_time_keyboard: Скрывать клавиатуру после использования (по умолчанию True).
    :param resize_keyboard: Автоматически изменять размер клавиатуры (по умолчанию True).
    :return: Объект ReplyKeyboardMarkup.
    """
    return ReplyKeyboardMarkup(
        [buttons[i:i + row_width] for i in range(0, len(buttons), row_width)],
        one_time_keyboard=one_time_keyboard,
        resize_keyboard=resize_keyboard
    )


def create_inline_keyboard(buttons, row_width=2):
    """
    Создает Inline-клавиатуру.

    :param buttons: Список списков кнопок (каждый внутренний список — это строка кнопок).
    :param row_width: Количество кнопок в строке (по умолчанию 2).
    :return: Объект InlineKeyboardMarkup.
    """
    return InlineKeyboardMarkup(buttons)


async def add_student(update: Update, context: CallbackContext):
    markup = create_reply_keyboard(['Вернуться в меню'], row_width=1)
    await update.message.reply_text("Введите имя ученика или нажмите 'Вернуться в меню':", reply_markup=markup)
    return TYPING_NAME


# Обработка выбора в меню администратора
async def handle_choice(update: Update, context: CallbackContext):
    choice = update.message.text  # Текст выбранной кнопки

    if choice == 'Добавить ученика':
        return await add_student(update, context)
    elif choice == 'Удалить ученика':
        return await delete_student(update, context)
    elif choice == 'Выдать домашнее задание':
        await update.message.reply_text("Вы можете выдать домашнее задание!")
        return await give_homework(update, context)
    elif choice == 'Добавить вариант':
        return await add_variant(update, context)
    elif choice == 'Внести изменения':
        return await modify_student(update, context)
    elif choice == 'Информация об ученике':
        return await show_student_info(update, context)
    elif choice == 'Работа с домашним заданием и конспектами':  # Новая кнопка
        return await handle_homework_and_notes_menu(update, context)
    elif choice == 'Назад':  # Обработка кнопки "Назад"
        return await handle_back_to_main_menu(update, context)
    elif choice in ['Добавить домашнее задание', "Изменить домашнее задание", "Удалить домашнее задание",
                    "Добавить конспект", "Изменить конспект", "Удалить конспект"]:
        # Обработка действий из подменю
        if choice == 'Добавить домашнее задание':
            return await handle_task_exam(update, context)
        elif choice == 'Изменить домашнее задание':
            return await start_edit_task(update, context)
        elif choice == 'Удалить домашнее задание':
            return await handle_delete_task_exam(update, context)
        elif choice == 'Добавить конспект':
            return await handle_note_exam(update, context)
        elif choice == 'Изменить конспект':
            return await start_edit_note(update, context)
        elif choice == 'Удалить конспект':
            return await handle_delete_note_exam(update, context)
    else:
        await update.message.reply_text("Я не ожидал такого действия. Попробуйте снова.")
        return CHOOSING


# Основная логика старта
async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start."""
    # Сбрасываем данные пользователя и начинаем с нуля
    context.user_data.clear()
    user_id = update.message.from_user.id

    if user_id in ADMIN_IDS:
        # Администраторское меню
        return await return_to_menu(update, context)
    else:
        # Логика для учеников
        user = get_user_by_telegram_id(user_id)
        if user:
            user_id, name, exam = user
            await update.message.reply_text(f"Добро пожаловать, {name}!\nВы зарегистрированы на экзамен: {exam}.")
            return await student_menu(update, context)
        else:
            await update.message.reply_text("Добро пожаловать в личный кабинет ученика. Введите пароль для входа:")
            return STUDENT_LOGIN


async def return_to_menu(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id

    if user_id in ADMIN_IDS:
        # Меню администратора с реплай-кнопками
        reply_markup = ReplyKeyboardMarkup(
            [
                ['Выдать домашнее задание', 'Добавить вариант'],
                ['Внести изменения', "Информация об ученике"],
                ['Добавить ученика', 'Удалить ученика'],
                ['Работа с домашним заданием и конспектами']  # Новая кнопка
            ],
            resize_keyboard=True
        )
        message = "Вы в меню администратора:"

        # Если это callback_query (нажатие на инлайн-кнопку)
        if update.callback_query:
            # Проверяем, что сообщение доступно и является доступным типом
            if update.callback_query.message and isinstance(update.callback_query.message, Message):
                # Удаляем старое сообщение с инлайн-кнопками
                await context.bot.delete_message(
                    chat_id=update.callback_query.message.chat_id,
                    message_id=update.callback_query.message.message_id
                )

            # Отправляем новое сообщение с реплай-кнопками
            await context.bot.send_message(
                chat_id=update.callback_query.from_user.id,
                text=message,
                reply_markup=reply_markup
            )
        else:
            # Если это обычное сообщение
            await update.message.reply_text(message, reply_markup=reply_markup)

        return CHOOSING  # Возвращаем состояние CHOOSING
    else:
        # Меню ученика
        return await student_menu(update, context)

# Добавьте новое состояние в список состояний
HOMEWORK_AND_NOTES_MENU = "HOMEWORK_AND_NOTES_MENU"


# Обработчик для кнопки "Работа с домашним заданием и конспектами"
async def handle_homework_and_notes_menu(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardMarkup(
        [
            ['Добавить домашнее задание', "Изменить домашнее задание", "Удалить домашнее задание"],
            ['Добавить конспект', "Изменить конспект", "Удалить конспект"],
            ['Назад']  # Кнопка для возврата в основное меню
        ],
        resize_keyboard=True
    )
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    return HOMEWORK_AND_NOTES_MENU


async def handle_back_to_main_menu(update: Update, context: CallbackContext):
    return await return_to_menu(update, context)


async def return_to_student_menu_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Закрываем всплывающее уведомление

    # Возвращаем ученика в меню
    return await student_menu(update, context)


# Обработка ввода имени ученика
async def handle_name(update: Update, context: CallbackContext):
    if update.message.text == 'Вернуться в меню':
        context.user_data.clear()  # Очищаем данные пользователя
        return await return_to_menu(update, context)

    # Сохраняем имя ученика в контексте
    context.user_data['student_name'] = update.message.text

    # Обновленная клавиатура с тремя вариантами
    markup = ReplyKeyboardMarkup(
        [['ОГЭ'], ['ЕГЭ'], ['Школьная программа'], ['Вернуться в меню']],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text(
        "Выберите экзамен (ОГЭ, ЕГЭ или Школьная программа) или нажмите 'Вернуться в меню':",
        reply_markup=markup
    )
    return TYPING_EXAM


# Обработка выбора экзамена
async def handle_exam_choice(update: Update, context: CallbackContext):
    if update.message.text == 'Вернуться в меню':
        context.user_data.clear()
        return await return_to_menu(update, context)

    exam = update.message.text
    if exam not in ['ОГЭ', 'ЕГЭ', 'Школьная программа']:
        await update.message.reply_text("Выберите действительный вариант (ОГЭ, ЕГЭ или Школьная программа).")
        return TYPING_EXAM

    context.user_data['exam'] = exam

    # Запрашиваем дату занятия
    await update.message.reply_text("Введите дату занятия в формате dd.mm.yyyy:")
    return TYPING_CLASS_DATE


async def handle_class_date(update: Update, context: CallbackContext):
    class_date = update.message.text
    try:
        # Проверяем формат даты
        datetime.datetime.strptime(class_date, "%d.%m.%Y")
    except ValueError:
        await update.message.reply_text("Неверный формат даты. Попробуйте снова (например, 25.12.2023):")
        return TYPING_CLASS_DATE

    context.user_data['class_date'] = class_date
    await update.message.reply_text("Введите ссылку для подключения к занятию:")
    return TYPING_CLASS_LINK


async def handle_class_link(update: Update, context: CallbackContext):
    class_link = update.message.text
    student_name = context.user_data.get('student_name')
    exam = context.user_data.get('exam')
    class_date = context.user_data.get('class_date')  # Получаем дату занятия из контекста

    if not student_name or not exam or not class_date:
        await update.message.reply_text("Ошибка: данные не найдены. Попробуйте снова.")
        return await return_to_menu(update, context)

    # Генерация пароля и сохранение ученика в базу данных
    password = add_user(student_name, exam)
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET class_link = ?, class_date = ? WHERE name = ? AND exam = ?',
            (class_link, class_date, student_name, exam)
        )
        conn.commit()

    await update.message.reply_text(
        f"Ученик добавлен:\n"
        f"Имя: {student_name}\n"
        f"Экзамен: {exam}\n"
        f"Дата занятия: {class_date}\n"
        f"Ссылка на занятие: {class_link}\n"
        f"Пароль: {password}\n"
        "Сообщите эту информацию ученику."
    )

    context.user_data.clear()  # Очищаем данные пользователя
    return await return_to_menu(update, context)


# Обработка кнопки "Удалить ученика"
async def delete_student(update: Update, context: CallbackContext):
    students = get_all_users()
    if not students:
        await update.message.reply_text("Нет зарегистрированных учеников.")
        return await return_to_menu(update, context)

    # Формируем Inline-клавиатуру с именами учеников
    buttons = [
        [InlineKeyboardButton(student[1], callback_data=f"delete_student:{student[0]}")]
        for student in students
    ]
    buttons.append([InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")])
    reply_markup = create_inline_keyboard(buttons, row_width=1)

    await update.message.reply_text("Выберите ученика для удаления или вернитесь в меню:", reply_markup=reply_markup)
    return None


# Обработка выбора для удаления ученика
async def handle_delete_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == "return_to_menu":
        await query.answer("Возврат в меню.")
        await return_to_menu(update, context)
        return CHOOSING  # Возвращаемся в состояние CHOOSING

    if data.startswith("delete_student:"):
        student_id = int(data.split(":")[1])

        # Получаем информацию об ученике (включая описание)
        with sqlite3.connect('your_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name, exam, description FROM users WHERE id = ?', (student_id,))
            student = cursor.fetchone()

            if not student:
                await query.answer("Ученик не найден.")
                return CHOOSING  # Возвращаемся в состояние CHOOSING

            # Распаковка данных ученика
            name, exam, description = student
            description_text = f"\nОписание: {description}" if description else ""

            # Удаляем ученика из базы данных
            cursor.execute('DELETE FROM users WHERE id = ?', (student_id,))
            conn.commit()

        # Отправляем сообщение об удалении ученика
        await query.answer()
        await query.edit_message_text(f"Ученик {name} с экзаменом {exam} был удален.{description_text}")

        # Возвращаемся в меню администратора
        await return_to_menu(update, context)
        return CHOOSING  # Возвращаемся в состояние CHOOSING


async def give_homework(update: Update, context: CallbackContext):
    students = get_all_users()
    if not students:
        await update.message.reply_text("Нет зарегистрированных учеников.")
        return

    # Создаем инлайн-клавиатуру с именами учеников
    buttons = [
        [InlineKeyboardButton(student[1], callback_data=f"select_student:{student[0]}")]
        for student in students
    ]
    buttons.append([InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")])
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text("Выберите ученика для выдачи задания:", reply_markup=reply_markup)


# Обработка выбора ученика
async def handle_select_student(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == "return_to_menu":
        await query.answer("Возврат в меню.")
        return

    # Обработка выбора ученика
    selected_student_id = int(data.split(":")[1])

    # Получаем данные ученика
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT exam FROM users WHERE id = ?', (selected_student_id,))
        result = cursor.fetchone()

    if not result:
        await query.answer("Ошибка: данные ученика не найдены.")
        return

    exam = result[0]

    # Если экзамен — "Школьная программа", запрашиваем ссылку на задание
    if exam == "Школьная программа":
        # Сохраняем ID ученика в context.user_data
        context.user_data['selected_student_id'] = selected_student_id
        print(f"ID ученика сохранен в context.user_data: {selected_student_id}")

        # Запрашиваем ввод ссылки
        await query.answer()
        await query.edit_message_text("Введите ссылку на задание:")

        # Переходим к состоянию HOMEWORK_LINK
        return HOMEWORK_LINK

    # Для других экзаменов (ОГЭ/ЕГЭ) можно добавить свою логику
    await query.answer()
    await handle_assign_homework(update, context, selected_student_id, exam)


async def handle_homework_link(update: Update, context: CallbackContext):
    # Получаем текст сообщения (ссылку)
    link = update.message.text

    # Сохраняем ссылку в context.user_data
    context.user_data['homework_link'] = link
    print(f"Ссылка сохранена в context.user_data: {link}")

    # Запрашиваем подтверждение
    markup = ReplyKeyboardMarkup([['Да', 'Нет']], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        f"Вы ввели ссылку: {link}. Сохранить её?",
        reply_markup=markup
    )

    # Переходим к состоянию подтверждения
    return CONFIRM_HOMEWORK_LINK


async def handle_confirm_homework_link(update: Update, context: CallbackContext):
    confirmation = update.message.text
    selected_student_id = context.user_data.get('selected_student_id')
    homework_link = context.user_data.get('homework_link')

    if confirmation == "Да":
        # Сохраняем задание в базе данных для ученика
        try:
            with sqlite3.connect('your_database.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE users SET homework = ? WHERE id = ?',
                    (homework_link, selected_student_id)
                )
                conn.commit()

            await update.message.reply_text("Задание успешно добавлено!")

            # Уведомляем ученика о новом задании (если у него есть telegram_id)
            with sqlite3.connect('your_database.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT telegram_id FROM users WHERE id = ?', (selected_student_id,))
                result = cursor.fetchone()

            if result and result[0]:
                try:
                    # Создаем клавиатуру с двумя кнопками
                    keyboard = [
                        [InlineKeyboardButton("Открыть задание", url=homework_link)],  # Кнопка со ссылкой
                        [InlineKeyboardButton("Вернуться в меню", callback_data="return_to_student_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    # Отправляем сообщение с кнопками
                    await context.bot.send_message(
                        chat_id=result[0],
                        text=f"У вас новое домашнее задание. Нажмите на кнопку ниже, чтобы открыть:",
                        reply_markup=reply_markup
                    )
                    print(f"Уведомление отправлено ученику с ID {result[0]}.")
                except Exception as e:
                    print(f"Не удалось уведомить ученика: {e}")
            else:
                print("У ученика нет telegram_id.")
        except sqlite3.Error as e:
            await update.message.reply_text(f"Ошибка при добавлении задания: {e}")
            print(f"Ошибка при сохранении в базу данных: {e}")
    else:
        await update.message.reply_text("Ссылка не сохранена.")

    # Очищаем context.user_data
    context.user_data.pop('selected_student_id', None)
    context.user_data.pop('homework_link', None)

    # Возвращаем пользователя в меню
    await return_to_menu(update, context)

    # Завершаем диалог
    return ConversationHandler.END


async def handle_assign_homework(update: Update, context: CallbackContext, selected_student_id: int, exam: str):
    # Получаем список заданий для выбранного экзамена
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, title FROM tasks WHERE exam_type = ?', (exam,))
        homework_options = cursor.fetchall()

    if not homework_options:
        await update.callback_query.edit_message_text(f"Для экзамена {exam} нет доступных заданий.")
        return

    # Создаем инлайн-клавиатуру с заданиями
    buttons = [
        [InlineKeyboardButton(title, callback_data=f"assign_homework:{task_id}")]
        for task_id, title in homework_options
    ]
    buttons.append([InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")])
    reply_markup = InlineKeyboardMarkup(buttons)

    # Сохраняем ID ученика в context.user_data
    context.user_data['selected_student_id'] = selected_student_id

    # Отправляем сообщение с заданиями
    await update.callback_query.edit_message_text(
        f"Выберите задание для ученика (экзамен: {exam}):",
        reply_markup=reply_markup
    )


# Обработка выбора задания
async def handle_assign_homework_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == "return_to_menu":
        await query.answer("Возврат в меню.")
        return

    # Обработка выбора задания
    task_id = int(data.split(":")[1])
    selected_student_id = context.user_data.get('selected_student_id')

    # if not selected_student_id:
    #     await query.answer("Ой, что-то пошло не так, нажми /start")
    #     return

    # Получаем данные задания
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT title, link FROM tasks WHERE id = ?', (task_id,))
        task = cursor.fetchone()

    if not task:
        await query.answer("Ошибка: задание не найдено.")
        return

    task_title, task_link = task

    # Сохраняем задание в базе данных для ученика
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET homework = ? WHERE id = ?', (task_link, selected_student_id))
        conn.commit()

    # Уведомляем ученика о новом задании (если у него есть telegram_id)
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT telegram_id FROM users WHERE id = ?', (selected_student_id,))
        result = cursor.fetchone()

    if result and result[0]:
        try:
            keyboard = [[InlineKeyboardButton("Открыть задание", url=task_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=result[0],
                text=f"У вас новое домашнее задание: {task_title}. Нажмите на кнопку ниже, чтобы открыть:",
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Не удалось уведомить ученика: {e}")

    # Сообщение для администратора
    await query.answer()
    await query.edit_message_text(f"Задание '{task_title}' назначено ученику.")


async def receive_homework(update: Update, context: CallbackContext):
    student_name = context.user_data.get('selected_student')
    # Если ученик выбран, сохраняем задание
    if student_name:
        if update.message.text:
            homework = update.message.text
            await update.message.reply_text(
                f"Задание для {student_name} сохранено:\n{homework}\nВозврат в меню."
            )

        # Удаляем данные о выбранном ученике из user_data
        context.user_data.pop('selected_student', None)

        # Возвращаемся в меню
        return await return_to_menu(update, context)

    await update.message.reply_text("Произошла ошибка. Попробуйте снова.")
    return await return_to_menu(update, context)


# Функция для обработки нажатия на кнопку "Добавить вариант"
async def add_variant(update: Update, context: CallbackContext):
    markup = ReplyKeyboardMarkup([['ОГЭ', 'ЕГЭ'], ['Вернуться в меню']], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите экзамен для добавления варианта:", reply_markup=markup)
    return ADD_VARIANT


# Обработка выбора экзамена для добавления варианта
async def handle_variant_exam(update: Update, context: CallbackContext):
    if update.message.text == 'Вернуться в меню':
        return await return_to_menu(update, context)

    exam = update.message.text
    if exam not in ['ОГЭ', 'ЕГЭ']:
        await update.message.reply_text("Выберите действительный экзамен (ОГЭ или ЕГЭ).")
        return ADD_VARIANT

    context.user_data['variant_exam'] = exam
    await update.message.reply_text(f"Вы выбрали {exam}. Пришлите ссылку на вариант:")
    return ADD_VARIANT_LINK


async def handle_variant_link(update: Update, context: CallbackContext):
    link = update.message.text
    exam = context.user_data.get('variant_exam')

    if not exam:
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")
        return await return_to_menu(update, context)

    # Сохраняем или обновляем вариант в базе данных
    db_execute('''
        INSERT INTO variants (exam, link) 
        VALUES (?, ?)
        ON CONFLICT(exam) DO UPDATE SET link = excluded.link
    ''', (exam, link))

    # Уведомляем всех учеников, относящихся к этому экзамену
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT telegram_id FROM users WHERE exam = ?', (exam,))
        students = cursor.fetchall()

    for student in students:
        telegram_id = student[0]
        if telegram_id:
            try:
                # Создаем клавиатуру с двумя кнопками
                keyboard = [
                    [InlineKeyboardButton("Открыть вариант", url=link)],  # Кнопка со ссылкой
                    [InlineKeyboardButton("Вернуться в меню", callback_data="return_to_student_menu")]
                    # Кнопка для возврата
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Отправляем сообщение с кнопками
                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=f"У вас обновился вариант экзамена ({exam}). Нажмите на кнопку ниже, чтобы открыть:",
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"Не удалось уведомить ученика с ID {telegram_id}: {e}")

    await update.message.reply_text(f"Ссылка на вариант для {exam} успешно добавлена или обновлена!")
    return await return_to_menu(update, context)


# Функция для выбора поля
async def modify_student(update: Update, context: CallbackContext):
    students = get_all_users()
    if not students:
        await update.message.reply_text("Нет зарегистрированных учеников.")
        return await return_to_menu(update, context)

    # Создаём клавиатуру с учениками
    keyboard = [[InlineKeyboardButton(student[1], callback_data=f"edit_student:{student[0]}")] for student in students]
    keyboard.append([InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите ученика для изменения данных или вернитесь в меню:",
                                    reply_markup=reply_markup)
    return None


async def handle_edit_student(update: Update, context: CallbackContext):
    query = update.callback_query
    student_id = int(query.data.split(":")[1])
    context.user_data['editing_student_id'] = student_id  # Сохраняем ID ученика

    # Получаем информацию об ученике
    student_info = get_student_info(student_id)
    if not student_info:
        await query.answer("Ошибка: ученик не найден.")
        return

    name = student_info["name"]
    exam = student_info["exam"]
    class_date = student_info["class_date"] or "Не указана"
    class_link = student_info["class_link"] or "Не указана"
    description = student_info["description"] or "Не указана"

    # Формируем сообщение с текущей информацией
    info_message = (
        f"Текущая информация об ученике:\n"
        f"Имя: {name}\n"
        f"Экзамен: {exam}\n"
        f"Дата занятия: {class_date}\n"
        f"Ссылка на занятие: {class_link}\n"
        f"Описание: {description}\n\n"
        f"Выберите, что вы хотите изменить:"
    )

    keyboard = [
        [InlineKeyboardButton("Имя", callback_data="edit_field:name")],
        [InlineKeyboardButton("Экзамен", callback_data="edit_field:exam")],
        [InlineKeyboardButton("Дата занятия", callback_data="edit_field:class_date")],
        [InlineKeyboardButton("Ссылка на занятие", callback_data="edit_field:class_link")],
        [InlineKeyboardButton("Добавить описание", callback_data="edit_field:description")],
        [InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(info_message, reply_markup=reply_markup)


# Обработка подтверждения изменений
async def handle_confirmation(update: Update, context: CallbackContext):
    confirmation = update.message.text
    student_id = context.user_data.get('editing_student_id')
    field = context.user_data.get('editing_field')
    new_value = context.user_data.get('new_value')

    if confirmation == "Да":
        try:
            with sqlite3.connect('your_database.db') as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE users SET {field} = ? WHERE id = ?", (new_value, student_id))
                conn.commit()

            await update.message.reply_text("Данные успешно обновлены!")
        except sqlite3.Error as e:
            await update.message.reply_text(f"Ошибка при обновлении базы данных: {e}")
    else:
        await update.message.reply_text("Изменение данных отменено.")

    context.user_data.clear()  # Очищаем контекст
    return await return_to_menu(update, context)


async def handle_delete_description(update: Update, context: CallbackContext):
    # Получаем ID ученика из контекста
    student_id = context.user_data.get('editing_student_id')
    if not student_id:
        await update.message.reply_text("Ошибка: ID ученика не найден.")
        return

    # Удаляем описание (устанавливаем NULL)
    update_student_field(student_id, "description", None)

    # Сообщаем пользователю об удалении описания
    await update.message.reply_text("Описание удалено. Вы возвращены в меню.")
    await return_to_menu(update, context)


async def show_student_info(update: Update, context: CallbackContext):
    students = get_all_users()  # Извлекаем всех учеников
    if not students:
        await update.message.reply_text("Нет зарегистрированных учеников.")
        return await return_to_menu(update, context)

    # Создаём Inline-клавиатуру для выбора ученика
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"{student[1]}",  # Имя ученика
                callback_data=f"show_info:{student[0]}"  # ID ученика
            )
        ]
        for student in students
    ]
    keyboard.append([InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Выберите ученика для просмотра информации или вернитесь в меню:",
        reply_markup=reply_markup
    )


async def handle_task_exam(update: Update, context: CallbackContext):
    if update.message.text == 'Вернуться в меню':
        return await return_to_menu(update, context)

    if update.message.text not in ['ОГЭ', 'ЕГЭ']:
        markup = create_reply_keyboard(['ОГЭ', 'ЕГЭ', 'Вернуться в меню'], row_width=2)
        await update.message.reply_text("Выберите действительный экзамен (ОГЭ или ЕГЭ):", reply_markup=markup)
        return ADD_TASK

    exam = update.message.text
    context.user_data['task_exam'] = exam
    await update.message.reply_text(f"Вы выбрали {exam}. Теперь введите название задания:")
    return ADD_TASK_TITLE


async def handle_task_title(update: Update, context: CallbackContext):
    """
    Обрабатывает ввод названия задания.
    Проверяет, уникально ли название для указанного экзамена.
    """
    title = update.message.text
    exam_type = context.user_data.get('task_exam')

    if not exam_type:
        await update.message.reply_text("Ошибка: тип экзамена не найден. Попробуйте снова.")
        return await return_to_menu(update, context)

    # Проверяем, уникально ли название задания
    if not is_task_title_unique(title, exam_type):
        await update.message.reply_text(
            f"Задание с названием '{title}' уже существует для экзамена {exam_type}. "
            "Пожалуйста, введите другое название:"
        )
        return ADD_TASK_TITLE  # Остаемся в состоянии ADD_TASK_TITLE для повторного ввода

    # Если название уникально, сохраняем его и запрашиваем ссылку
    context.user_data['task_title'] = title
    await update.message.reply_text("Название задания сохранено. Теперь пришлите ссылку на задание:")
    return ADD_TASK_LINK


async def handle_task_link(update: Update, context: CallbackContext):
    """
    Шаг 3: Обработка ввода ссылки и сохранение задания.
    """
    link = update.message.text
    exam = context.user_data.get('task_exam')
    title = context.user_data.get('task_title')

    if not exam or not title:
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")
        return await return_to_menu(update, context)

    # Сохраняем задание в базу данных
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tasks (title, link, exam_type) VALUES (?, ?, ?)', (title, link, exam))
        conn.commit()

    await update.message.reply_text(f"Задание '{title}' для {exam} успешно добавлено!")
    return await return_to_menu(update, context)


async def handle_delete_task_exam(update: Update, context: CallbackContext):
    """
    Шаг 1: Выбор экзамена для удаления задания через инлайн-кнопки.
    """
    keyboard = [
        [InlineKeyboardButton("ОГЭ", callback_data="delete_exam:ОГЭ")],
        [InlineKeyboardButton("ЕГЭ", callback_data="delete_exam:ЕГЭ")],
        [InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Выберите экзамен, задания которого хотите удалить:",
        reply_markup=reply_markup
    )
    return None


async def handle_select_task_to_delete_callback(update: Update, context: CallbackContext):
    """
    Шаг 2: Выбор задания для удаления через инлайн-кнопки.
    """
    query = update.callback_query
    exam = query.data.split(":")[1]

    # Сохраняем выбранный экзамен
    context.user_data['selected_exam'] = exam

    # Загружаем задания из базы данных
    tasks = get_tasks_by_exam(exam)

    if not tasks:
        await query.answer()  # Закрываем всплывающее уведомление

        # Отправляем сообщение об отсутствии заданий
        if query.message:
            await query.edit_message_text(f"Нет доступных заданий для экзамена {exam}.")
        else:
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=f"Нет доступных заданий для экзамена {exam}."
            )

    # Формируем Inline-клавиатуру с заданиями
    keyboard = [
        [InlineKeyboardButton(title, callback_data=f"delete_task:{task_id}")]
        for task_id, title, _ in tasks
    ]
    keyboard.append([InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text(
        f"Выберите задание для удаления ({exam}):",
        reply_markup=reply_markup
    )
    return None


async def handle_task_deletion_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == "return_to_menu":
        await query.answer("Возврат в меню.")
        # Очищаем context.user_data
        context.user_data.clear()
        # Возвращаем пользователя в главное меню
        return await return_to_menu(update, context)

    if data.startswith("delete_task:"):
        task_id = int(data.split(":")[1])

        # Удаляем задание из базы данных
        with sqlite3.connect('your_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT title FROM tasks WHERE id = ?', (task_id,))
            task = cursor.fetchone()

            if not task:
                await query.answer("Ошибка: задание не найдено.")
                return None

            task_title = task[0]
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()

        # Сообщение об успешном удалении
        await query.answer()
        if query.message:
            await query.edit_message_text(f"Задание '{task_title}' было успешно удалено.")
        else:
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=f"Задание '{task_title}' было успешно удалено."
            )

        # Очищаем context.user_data
        context.user_data.clear()

        # Возвращаем пользователя в главное меню
        await return_to_menu(update, context)
        return ConversationHandler.END


# Начало процесса редактирования
async def start_edit_task(update: Update, context: CallbackContext):
    buttons = [
        [InlineKeyboardButton("ОГЭ", callback_data="exam:ОГЭ")],
        [InlineKeyboardButton("ЕГЭ", callback_data="exam:ЕГЭ")],
        [InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]
    ]
    reply_markup = create_inline_keyboard(buttons, row_width=2)
    await update.message.reply_text("Выберите экзамен:", reply_markup=reply_markup)
    return EDIT_TASK_CHOOSE_EXAM


# Обработка выбора экзамена
async def choose_exam(update: Update, context: CallbackContext):
    query = update.callback_query
    exam_type = query.data.split(":")[1]
    context.user_data['exam_type'] = exam_type

    tasks = get_tasks_by_exam(exam_type)
    if not tasks:
        await query.edit_message_text(f"Нет заданий для экзамена {exam_type}.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(task[1], callback_data=f"task:{task[0]}")] for task in tasks
    ]
    keyboard.append([InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")])  # Добавляем кнопку
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите задание для редактирования:", reply_markup=reply_markup)
    return EDIT_TASK_CHOOSE_TASK


# Обработка выбора задания
async def choose_task(update: Update, context: CallbackContext):
    query = update.callback_query
    task_id = int(query.data.split(":")[1])
    context.user_data['task_id'] = task_id

    buttons = [
        [InlineKeyboardButton("Название", callback_data="field:title")],
        [InlineKeyboardButton("Ссылка", callback_data="field:link")],
        [InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]
    ]
    reply_markup = create_inline_keyboard(buttons, row_width=2)
    await query.edit_message_text("Что вы хотите изменить?", reply_markup=reply_markup)
    return EDIT_TASK_CHOOSE_FIELD


# Обработка выбора поля
async def choose_field(update: Update, context: CallbackContext):
    query = update.callback_query
    field = query.data.split(":")[1]
    context.user_data['field'] = field

    # Добавляем кнопку "Вернуться в меню" в текстовом сообщении
    markup = ReplyKeyboardMarkup([['Вернуться в меню']], one_time_keyboard=True, resize_keyboard=True)
    await query.edit_message_text(f"Введите новое значение для {field}:")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Или нажмите 'Вернуться в меню':",
                                   reply_markup=markup)
    return EDIT_TASK_UPDATE_FIELD


# Обработка ввода нового значения
async def update_task_field(update: Update, context: CallbackContext):
    new_value = update.message.text
    context.user_data['new_value'] = new_value

    markup = ReplyKeyboardMarkup([['Да', 'Нет']], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(f"Вы ввели: {new_value}. Подтвердить изменения?", reply_markup=markup)
    return EDIT_TASK_CONFIRM_UPDATE  # Возвращаем новое состояние


# Подтверждение изменений
async def confirm_task_update(update: Update, context: CallbackContext):
    confirmation = update.message.text
    if confirmation == "Да":
        task_id = context.user_data.get('task_id')
        field = context.user_data.get('field')
        new_value = context.user_data.get('new_value')

        try:
            with sqlite3.connect('your_database.db') as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE tasks SET {field} = ? WHERE id = ?", (new_value, task_id))
                conn.commit()

            await update.message.reply_text("Задание успешно обновлено!")
        except sqlite3.Error as e:
            await update.message.reply_text(f"Ошибка при обновлении базы данных: {e}")
    else:
        await update.message.reply_text("Изменения отменены.")

    # Очищаем контекст
    context.user_data.clear()

    # Возвращаем пользователя в главное меню
    return await return_to_menu(update, context)


async def handle_return_to_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Закрываем всплывающее уведомление

    # Очищаем context.user_data
    context.user_data.clear()

    # Возвращаем состояние CHOOSING
    return await return_to_menu(update, context)


async def handle_note_exam(update: Update, context: CallbackContext):
    if update.message.text == 'Вернуться в меню':
        return await return_to_menu(update, context)

    if update.message.text not in ['ОГЭ', 'ЕГЭ']:
        markup = create_reply_keyboard(['ОГЭ', 'ЕГЭ', 'Вернуться в меню'], row_width=2)
        await update.message.reply_text("Выберите действительный экзамен (ОГЭ или ЕГЭ):", reply_markup=markup)
        return ADD_NOTE

    exam = update.message.text
    context.user_data['note_exam'] = exam
    await update.message.reply_text(f"Вы выбрали {exam}. Теперь введите название конспекта:")
    return ADD_NOTE_TITLE


async def handle_note_title(update: Update, context: CallbackContext):
    title = update.message.text
    exam_type = context.user_data.get('note_exam')

    if not exam_type:
        await update.message.reply_text("Ошибка: тип экзамена не найден. Попробуйте снова.")
        return await return_to_menu(update, context)

    # Проверяем, уникально ли название конспекта
    if not is_note_title_unique(title, exam_type):
        await update.message.reply_text(
            f"Конспект с названием '{title}' уже существует для экзамена {exam_type}. "
            "Пожалуйста, введите другое название:"
        )
        return ADD_NOTE_TITLE

    context.user_data['note_title'] = title
    await update.message.reply_text("Название конспекта сохранено. Теперь пришлите ссылку на конспект:")
    return ADD_NOTE_LINK


async def handle_note_link(update: Update, context: CallbackContext):
    link = update.message.text
    exam = context.user_data.get('note_exam')
    title = context.user_data.get('note_title')

    if not exam or not title:
        await update.message.reply_text("Ошибка: данные не найдены. Попробуйте снова.")
        return await return_to_menu(update, context)

    # Сохраняем конспект в базу данных
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO notes (title, link, exam_type) VALUES (?, ?, ?)', (title, link, exam))
        conn.commit()

    await update.message.reply_text(f"Конспект '{title}' для {exam} успешно добавлен!")

    # Очищаем context.user_data
    context.user_data.clear()

    # Возвращаемся в меню
    return await return_to_menu(update, context)


async def handle_delete_note_exam(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("ОГЭ", callback_data="delete_note_exam:ОГЭ")],
        [InlineKeyboardButton("ЕГЭ", callback_data="delete_note_exam:ЕГЭ")],
        [InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Выберите экзамен, конспекты которого хотите удалить:",
        reply_markup=reply_markup
    )
    return None


async def handle_select_note_to_delete_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    exam = query.data.split(":")[1]

    # Сохраняем выбранный экзамен
    context.user_data['selected_exam'] = exam

    # Загружаем конспекты из базы данных
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, title FROM notes WHERE exam_type = ?', (exam,))
        notes = cursor.fetchall()

    if not notes:
        await query.answer()
        await query.edit_message_text(f"Нет доступных конспектов для экзамена {exam}.")
        context.user_data.clear()
        await return_to_menu(update, context)
        return ConversationHandler.END

    # Формируем Inline-клавиатуру с конспектами
    keyboard = [
        [InlineKeyboardButton(title, callback_data=f"delete_note:{note_id}")]
        for note_id, title in notes
    ]
    keyboard.append([InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text(
        f"Выберите конспект для удаления ({exam}):",
        reply_markup=reply_markup
    )
    return None


async def handle_note_deletion_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == "return_to_menu":
        await query.answer("Возврат в меню.")
        await return_to_menu(update, context)
        return ConversationHandler.END

    if data.startswith("delete_note:"):
        note_id = int(data.split(":")[1])

        # Удаляем конспект из базы данных
        with sqlite3.connect('your_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT title FROM notes WHERE id = ?', (note_id,))
            note = cursor.fetchone()

            if not note:
                await query.answer("Ошибка: конспект не найден.")
                await return_to_menu(update, context)
                return ConversationHandler.END

            note_title = note[0]
            cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
            conn.commit()

        # Сообщение об успешном удалении
        await query.answer()
        # Отправляем сообщение об успешном удалении
        if query.message:
            await query.edit_message_text(f"Конспект '{note_title}' был успешно удален.")
        else:
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=f"Конспект '{note_title}' был успешно удален."
            )

        # Очищаем context.user_data
        context.user_data.clear()

        # Возвращаемся в меню
        await return_to_menu(update, context)
        return ConversationHandler.END


async def start_edit_note(update: Update, context: CallbackContext):
    buttons = [
        [InlineKeyboardButton("ОГЭ", callback_data="note_exam:ОГЭ")],
        [InlineKeyboardButton("ЕГЭ", callback_data="note_exam:ЕГЭ")],
        [InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")]
    ]
    reply_markup = create_inline_keyboard(buttons, row_width=2)
    await update.message.reply_text("Выберите экзамен:", reply_markup=reply_markup)
    return EDIT_NOTE_CHOOSE_EXAM


async def choose_note_exam(update: Update, context: CallbackContext):
    query = update.callback_query
    exam_type = query.data.split(":")[1]
    context.user_data['note_exam'] = exam_type

    # Получаем конспекты для выбранного экзамена
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, title FROM notes WHERE exam_type = ?', (exam_type,))
        notes = cursor.fetchall()

    if not notes:
        await query.edit_message_text(f"Нет конспектов для экзамена {exam_type}.")
        return return_to_menu(update, context)  # Возвращаемся в меню

    # Формируем Inline-клавиатуру с конспектами
    keyboard = [
        [InlineKeyboardButton(title, callback_data=f"note:{note_id}")]
        for note_id, title in notes
    ]
    keyboard.append([InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите конспект для редактирования:", reply_markup=reply_markup)
    return EDIT_NOTE_CHOOSE_NOTE


async def choose_note(update: Update, context: CallbackContext):
    query = update.callback_query
    note_id = int(query.data.split(":")[1])
    context.user_data['note_id'] = note_id

    buttons = [
        [InlineKeyboardButton("Название", callback_data="note_field:title")],
        [InlineKeyboardButton("Ссылка", callback_data="note_field:link")],
        [InlineKeyboardButton("Вернуться в меню", callback_data="return_to_menu")],
    ]
    reply_markup = create_inline_keyboard(buttons, row_width=2)
    await query.edit_message_text("Что вы хотите изменить?", reply_markup=reply_markup)
    return EDIT_NOTE_CHOOSE_FIELD


async def choose_note_field(update: Update, context: CallbackContext):
    query = update.callback_query
    field = query.data.split(":")[1]
    context.user_data['note_field'] = field

    markup = ReplyKeyboardMarkup([['Вернуться в меню']], one_time_keyboard=True, resize_keyboard=True)
    await query.edit_message_text(f"Введите новое значение для {field}:")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Или нажмите 'Вернуться в меню':",
                                   reply_markup=markup)
    return EDIT_NOTE_UPDATE_FIELD


async def update_note_field(update: Update, context: CallbackContext):
    new_value = update.message.text
    context.user_data['new_value'] = new_value

    markup = ReplyKeyboardMarkup([['Да', 'Нет']], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(f"Вы ввели: {new_value}. Подтвердить изменения?", reply_markup=markup)
    return EDIT_NOTE_CONFIRM_UPDATE


async def confirm_note_update(update: Update, context: CallbackContext):
    confirmation = update.message.text  # Получаем ответ пользователя

    if confirmation == "Да":
        # Если пользователь подтвердил изменения
        note_id = context.user_data.get('note_id')
        field = context.user_data.get('note_field')
        new_value = context.user_data.get('new_value')

        if not note_id or not field or not new_value:
            await update.message.reply_text("Ошибка: данные не найдены. Попробуйте снова.")
            return await return_to_menu(update, context)

        try:
            with sqlite3.connect('your_database.db') as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE notes SET {field} = ? WHERE id = ?", (new_value, note_id))
                conn.commit()

            await update.message.reply_text("Конспект успешно обновлен!")
        except sqlite3.Error as e:
            await update.message.reply_text(f"Ошибка при обновлении базы данных: {e}")
    elif confirmation == "Нет":
        # Если пользователь отменил изменения
        await update.message.reply_text("Изменения отменены.")
    else:
        # Если пользователь ввел что-то другое
        await update.message.reply_text("Неизвестная команда. Изменения отменены.")

    # Очищаем context.user_data
    context.user_data.clear()

    # Возвращаем пользователя в меню
    return await return_to_menu(update, context)


def main():
    create_tables()

    # Ваш токен для бота
    application = Application.builder().token(BOT_TOKEN).build()

    # Определение ConversationHandler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex(
                        r"^(Добавить ученика|Удалить ученика|Выдать домашнее задание|Добавить вариант|Внести изменения|"
                        r"Информация об ученике|Работа с домашним заданием и конспектами)$"
                    ),
                    handle_choice
                )
            ],
            HOMEWORK_AND_NOTES_MENU: [
                MessageHandler(
                    filters.Regex(
                        r"^(Добавить домашнее задание|Изменить домашнее задание|Удалить домашнее задание|"
                        r"Добавить конспект|Изменить конспект|Удалить конспект|Назад)$"
                    ),
                    handle_choice
                )
            ],
            TYPING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            TYPING_EXAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_exam_choice)],
            STUDENT_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, student_login)],
            STUDENT_MENU: [
                MessageHandler(
                    filters.Regex(r"^(Домашнее задание|Конспекты|Актуальный вариант|Подключиться к занятию)$"),
                    handle_student_menu
                )
            ],
            ADD_VARIANT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_variant_exam)],
            ADD_VARIANT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_variant_link)],
            TYPING_CLASS_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_class_link)],
            TYPING_CLASS_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_class_date)],
            ADD_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_exam)],
            ADD_TASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_title)],
            ADD_TASK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_link)],
            ADD_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_note_exam)],
            ADD_NOTE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_note_title)],
            ADD_NOTE_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_note_link)],
            EDIT_NOTE_CHOOSE_EXAM: [
                CallbackQueryHandler(choose_note_exam, pattern=r"^note_exam:"),
                CallbackQueryHandler(handle_return_to_menu, pattern=r"^return_to_menu$")
            ],
            EDIT_NOTE_CHOOSE_NOTE: [
                CallbackQueryHandler(choose_note, pattern=r"^note:"),
                CallbackQueryHandler(handle_return_to_menu, pattern=r"^return_to_menu$")
            ],
            EDIT_NOTE_CHOOSE_FIELD: [
                CallbackQueryHandler(choose_note_field, pattern=r"^note_field:"),
                CallbackQueryHandler(handle_return_to_menu, pattern=r"^return_to_menu$")
            ],
            EDIT_NOTE_UPDATE_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_note_field),
                MessageHandler(filters.Regex("^Вернуться в меню$"), handle_return_to_menu)
            ],
            EDIT_NOTE_CONFIRM_UPDATE: [
                MessageHandler(filters.Regex("^(Да|Нет)$"), confirm_note_update),
                MessageHandler(filters.Regex("^Вернуться в меню$"), handle_return_to_menu)
            ],

            EDIT_TASK_CHOOSE_EXAM: [
                CallbackQueryHandler(choose_exam, pattern=r"^exam:"),
                CallbackQueryHandler(handle_return_to_menu, pattern=r"^return_to_menu$")
                # Обработчик для возврата в меню
            ],
            EDIT_TASK_CHOOSE_TASK: [
                CallbackQueryHandler(choose_task, pattern=r"^task:"),
                CallbackQueryHandler(handle_return_to_menu, pattern=r"^return_to_menu$")
                # Обработчик для возврата в меню
            ],
            EDIT_TASK_CHOOSE_FIELD: [
                CallbackQueryHandler(choose_field, pattern=r"^field:"),
                CallbackQueryHandler(handle_return_to_menu, pattern=r"^return_to_menu$")
                # Обработчик для возврата в меню
            ],
            EDIT_TASK_UPDATE_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_task_field),
                MessageHandler(filters.Regex("^Вернуться в меню$"), handle_return_to_menu)
                # Обработчик для возврата в меню
            ],
            EDIT_TASK_CONFIRM_UPDATE: [
                MessageHandler(filters.Regex("^(Да|Нет)$"), confirm_task_update),
                MessageHandler(filters.Regex("^Вернуться в меню$"), handle_return_to_menu)
                # Обработчик для возврата в меню
            ],
        },
        fallbacks=[CommandHandler('start', return_to_menu)],
    )

    modify_user_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_edit_student,  pattern=r"^edit_student:\d+$")],
        states={
                CHOOSING_FIELD: [CallbackQueryHandler(handle_edit_field,
                                                      pattern=r"^edit_field:(name|exam|class_date|class_link)$")],
                UPDATING_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_value)],
                CONFIRMATION: [MessageHandler(filters.Regex("^(Да|Нет)$"), handle_confirmation)]
                },
        fallbacks=[
            CommandHandler('start', return_to_menu)
        ]
    )

    homework_link_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_select_student, pattern=r"^select_student:\d+$")],
        # Начинаем с выбора ученика
        states={
            HOMEWORK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_homework_link)],
            # Ожидаем ввод ссылки
            CONFIRM_HOMEWORK_LINK: [MessageHandler(filters.Regex("^(Да|Нет)$"), handle_confirm_homework_link)]
            # Ожидаем подтверждение
        },
        fallbacks=[
            CommandHandler('start', return_to_menu)  # Возврат в меню в случае ошибки
        ]
    )

    # Добавление основного ConversationHandler
    application.add_handler(conversation_handler)  # Основной обработчик
    application.add_handler(modify_user_handler)  # Изолированный обработчик
    application.add_handler(homework_link_handler)
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_homework_link))

    # Обработчики для CallbackQuery
    application.add_handler(CallbackQueryHandler(handle_delete_callback, pattern=r"^delete_student:"))
    application.add_handler(CallbackQueryHandler(handle_select_student, pattern=r"^select_student:"))
    application.add_handler(CallbackQueryHandler(handle_assign_homework_callback, pattern=r"^assign_homework:"))
    application.add_handler(CallbackQueryHandler(handle_delete_callback, pattern="^return_to_menu$"))
    application.add_handler(CallbackQueryHandler(handle_edit_student, pattern=r"^edit_student:\d+$"))
    application.add_handler(CallbackQueryHandler(handle_edit_field, pattern=r"^edit_field:.*"))
    application.add_handler(CallbackQueryHandler(handle_new_exam, pattern=r"^new_exam:.*"))
    application.add_handler(CallbackQueryHandler(handle_show_student_info, pattern=r"^show_info:\d+$"))
    application.add_handler(CallbackQueryHandler(handle_select_task_to_delete_callback,
                                                 pattern=r"^delete_exam:(ОГЭ|ЕГЭ)$"))
    application.add_handler(CallbackQueryHandler(handle_task_deletion_callback, pattern=r"^delete_task:\d+$"))
    application.add_handler(
        CallbackQueryHandler(handle_select_note_to_delete_callback, pattern=r"^delete_note_exam:(ОГЭ|ЕГЭ)$"))
    application.add_handler(CallbackQueryHandler(handle_note_deletion_callback, pattern=r"^delete_note:\d+$"))
    application.add_handler(CallbackQueryHandler(choose_note_exam, pattern=r"^note_exam:"))
    application.add_handler(CallbackQueryHandler(choose_note, pattern=r"^note:"))
    application.add_handler(CallbackQueryHandler(choose_note_field, pattern=r"^note_field:"))

    application.add_handler(CallbackQueryHandler(return_to_student_menu, pattern="^return_to_menu$"))
    application.add_handler(CallbackQueryHandler(return_to_student_menu_callback, pattern="^return_to_student_menu$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_message_handler))
    application.add_handler(MessageHandler(filters.Regex("^/start$"), start))

    # Запуск приложения
    application.run_polling()


if __name__ == '__main__':
    main()

