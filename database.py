import sqlite3
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
                for student in students ]


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
