import time
import re
import random
import locale
from datetime import datetime

# Устанавливаем локаль на русский
locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

# Получаем текущие дату и время
current_time = time.strftime("%H:%M:%S")
current_day = datetime.today().strftime("%A")
current_date = datetime.today().strftime("%d.%m.%Y")

# База ответов на шаблонные вопросы
answers = {
    r"привет": "Привет! Чем могу помочь?",
    r"здравствуй": "Здравствуйте! Как могу помочь?",
    r"как тебя зовут\??": "Меня зовут Бот-Помощник!",
    r"что ты умеешь\??": "Я могу отвечать на вопросы о времени, дате и выполнять простые вычисления.",
    r"сколько времени\??": f"Сейчас {current_time}",
    r"какой сегодня день\??": f"Сегодня {current_day}",
    r"какое сегодня число\??": f"Сегодня {current_date}",
    r"какая сегодня дата\??": f"Сегодня {current_date}",
    r"какая погода\??": "Не знаю, но надеюсь, хорошая!",
    r"как дела\??": "Все отлично, спасибо за вопрос!",
    r"спасибо": "Рад помочь!",
}

def evaluate(expression):
    """Обрабатывает арифметическое выражение и возвращает результат"""
    try:
        expression = re.sub(r"\s+", "", expression)  # Убираем пробелы
        if not re.fullmatch(r"\d+[\+\-\*/]\d+", expression):
            return "Ошибка: некорректное выражение"
        return str(eval(expression))
    except ZeroDivisionError:
        return "Ошибка: деление на ноль невозможно"
    except Exception:
        return "Ошибка в вычислении"

def get_response(message):
    """Анализирует сообщение и возвращает ответ"""
    message = message.lower().strip()

    # Поиск совпадений в базе ответов
    for pattern, reply in answers.items():
        if re.search(pattern, message):
            return reply

    # Проверяем, просит ли пользователь вычислить выражение
    match = re.search(r"(?:вычисли|посчитай)\s*([\d+\-*/ ]+)", message)
    if match:
        return evaluate(match.group(1))

    # Если сообщение - это только арифметическое выражение
    if re.fullmatch(r"[\d+\-*/ ]+", message):
        return evaluate(message)

    return random.choice(["Не понял, попробуйте иначе.", "Повторите вопрос, пожалуйста."])

if __name__ == "__main__":
    print("Введите 'стоп' для выхода.")
    while True:
        user_input = input("Вы: ")
        if user_input.lower() == "стоп":
            print("Бот:", random.choice(["До свидания!", "Всего доброго!"]))
            break
        print("Бот:", get_response(user_input))
