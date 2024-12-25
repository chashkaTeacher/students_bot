import random
import string


# Функция для генерации случайного пароля
def generate_password(length=8):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
