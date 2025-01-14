import sqlite3
from natsort import natsorted
from utils import generate_password


def db_execute(query, params=(), fetchone=False, fetchall=False):
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
        conn.commit()


def create_tables():
    db_execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            exam TEXT,
            password TEXT,
            telegram_id INTEGER,
            homework TEXT,
            class_link TEXT
        )
    ''')

    db_execute('''
        CREATE TABLE IF NOT EXISTS variants (
            exam TEXT UNIQUE,
            link TEXT,
            class_date TEXT
        )
    ''')

    # Создаём таблицу для домашних заданий
    db_execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                exam_type TEXT NOT NULL
            )
        ''')

    db_execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                exam_type TEXT NOT NULL
            )
        ''')


def get_user_by_password(password):
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, exam FROM users WHERE password = ?', (password,))
        return cursor.fetchone()


def update_user_telegram_id(user_id, telegram_id):
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET telegram_id = ? WHERE id = ?', (telegram_id, user_id))
        conn.commit()


def get_all_users():
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, exam, description FROM users')  # Извлекаем все записи
        students = cursor.fetchall()
        return [(student[0], f"{student[1]} ({student[2]}) {student[3] if student[3] else ''}")
                for student in students]


def get_student_info(student_id):
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, exam, class_date, class_link, description, homework, telegram_id, password 
            FROM users 
            WHERE id = ?
        ''', (student_id,))
        student = cursor.fetchone()
        if student:
            return {
                "name": student[0],
                "exam": student[1],
                "class_date": student[2] or "Не указана",
                "class_link": student[3] or "Не указана",
                "description": student[4] or "Описание отсутствует",
                "homework": student[5] or "Нет задания",
                "telegram_id": student[6] or "Не указан",
                "password": student[7] or "Не установлен"
            }
        return None


# Функция для получения пользователя по Telegram ID
def get_user_by_telegram_id(telegram_id):
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, exam FROM users WHERE telegram_id = ?', (telegram_id,))
        return cursor.fetchone()


# Функция для удаления пользователя
def delete_user(name):
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT exam FROM users WHERE name = ?', (name,))
        result = cursor.fetchone()

        if not result:
            return None  # Если ученик с таким именем не найден

        exam = result[0]  # Извлекаем экзамен
        cursor.execute('DELETE FROM users WHERE name = ?', (name,))
        conn.commit()
        return exam


# Функция для добавления ученика
def add_user(name, exam):
    password = generate_password()  # Генерация случайного пароля
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, exam, password) VALUES (?, ?, ?)', (name, exam, password))
        conn.commit()
    return password  # Возвращаем пароль


def update_student_field(student_id, field, value):
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        if value is None:
            # Устанавливаем поле как NULL
            cursor.execute(f'UPDATE users SET {field} = NULL WHERE id = ?', (student_id,))
        else:
            # Обновляем поле с новым значением
            cursor.execute(f'UPDATE users SET {field} = ? WHERE id = ?', (value, student_id))
        conn.commit()


def update_password_to_id(user_id, telegram_id):
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password = ? WHERE id = ?', (str(telegram_id), user_id))
        conn.commit()


# Добавление нового задания в таблицу tasks.
def add_task(title, link, exam_type):
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tasks (title, link, exam_type) VALUES (?, ?, ?)',
                       (title, link, exam_type))
        conn.commit()


# Получение списка заданий для указанного типа экзамена.
def get_tasks_by_exam(exam_type):
    """
    Получение списка заданий для указанного типа экзамена, отсортированного естественным образом по названию.
    """
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, title, link FROM tasks WHERE exam_type = ?', (exam_type,)
        )
        tasks = cursor.fetchall()  # [(id, title, link), ...]

    # Естественная сортировка по названию
    return natsorted(tasks, key=lambda x: x[1])  # Сортируем по второму элементу (title)


def get_notes_by_exam(exam_type):
    """
    Получение списка конспектов для указанного типа экзамена, отсортированного естественным образом по названию.
    """
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, title, link FROM notes WHERE exam_type = ?', (exam_type,)
        )
        notes = cursor.fetchall()  # [(id, title, link), ...]

    # Естественная сортировка по названию
    return natsorted(notes, key=lambda x: x[1])  # Сортируем по второму элементу (title)


# Удаление задания из базы данных по ID.
def delete_task(task_id):
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()


# Получение задания по ID.
def get_task_by_id(task_id):
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, link FROM tasks WHERE id = ?', (task_id,))
        return cursor.fetchone()  # Кортеж: (id, title, link)


def is_task_title_unique(title, exam_type):
    """
    Проверяет, уникально ли название задания для указанного экзамена.

    :param title: Название задания.
    :param exam_type: Тип экзамена (ОГЭ/ЕГЭ).
    :return: True, если название уникально, иначе False.
    """
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tasks WHERE title = ? AND exam_type = ?", (title, exam_type))
        return cursor.fetchone() is None  # Если задание не найдено, возвращаем True


def is_note_title_unique(title: str, exam_type: str) -> bool:
    """
    Проверяет, уникально ли название конспекта для указанного экзамена.

    :param title: Название конспекта.
    :param exam_type: Тип экзамена (ОГЭ или ЕГЭ).
    :return: True, если название уникально, иначе False.
    """
    with sqlite3.connect('your_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM notes WHERE title = ? AND exam_type = ?', (title, exam_type))
        result = cursor.fetchone()
        return result is None  # Если результат пустой, название уникально
