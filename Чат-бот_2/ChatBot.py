import re
import random
import requests
from datetime import datetime
from googletrans import Translator
from textblob import TextBlob
import webbrowser

translator = Translator()
LOG_FILE = "chat.txt"

with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("=== Новый разговор ===\n")

def log_message(sender, message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{sender}: {message}\n")

DAYS_RU_LIST = [
    "понедельник", "вторник", "среда", "четверг", 
    "пятница", "суббота", "воскресенье"
]
API_KEY = "22b6c1843b73184829f5eec1bb60c502"

user_name = ""
waiting_for_city = False
waiting_for_talk = False

positive_keywords = ['доброе утро', 'хорошо', 'прекрасно', 'замечательно', 'отлично', 'рад']
negative_keywords = ['плохо', 'грустно', 'тяжело', 'депрессия', 'печально', 'погано', 'устала']

responses = {
    r"\bпривет\w*\b": [
        "Привет! 😊 Как твои дела?",
        "Здравствуйте! Чем могу помочь?",
        "Йо! Что нового?",
        "Салют! Рад тебя видеть 😄",
        "Приветики! Чем займёмся сегодня?",
        "О, ты вернулся! Как настроение?"],
    r"\bдела\w*|\bнастроение\w*": [
        "У меня всё отлично! А у тебя как?",
        "Прекрасно, особенно когда ты здесь! Как сам?",
        "Всё супер, спасибо, что спросил(а)! А ты как?",
        "Солнце светит, бот доволен! 😎 А у тебя как день?",
        "Настроение ботическое, как у тебя?"],
    r"\bможешь\w*": [
        "Я могу показать время, дату, погоду, найти в интернете и даже поддержать тебя!",
        "Спросишь — отвечу, захочешь — найду! Просто скажи.",
        "Я умею многое — от анекдота до прогноза погоды!",
        "Проверю погоду, посчитаю пример или просто поболтаю 🙂"],
    r"\bспасибо\w*|\bблагодарю\b": [
        "Всегда рад помочь! 😊",
        "Пожалуйста! Обращайся в любое время.",
        "Всегда к твоим услугам!",
        "Рад был помочь! 😌"],
    r"\bпока\w*|\bсвидания\w*": [
        "До скорой встречи! 👋",
        "Пока! Будь счастлив!",
        "Увидимся позже! Не забывай меня 🙂",
        "До встречи! Береги себя."],
    r"\bсейчас\s*время|\bсколько\s*время|\bчас\b": lambda _: datetime.now().strftime("Сейчас %H:%M."),
    r"\bдата\b|\bчисло\b": lambda _: datetime.now().strftime("Сегодня %d.%m.%Y."),
    r"\bдень\b": lambda _: f"Сегодня {DAYS_RU_LIST[datetime.now().weekday()]}.",
    r"\bанекдот\w*|\bшутк\w*|\bпошути\b": [
        "Что говорит голубь, когда вводит не ту ссылку в гугле? 'Неправильный урл'",
        "Почему программисты путают Хэллоуин и Рождество? OCT 31 = DEC 25.",
        "Как зовут кота-программиста? Котлин.",
        "У меня нет чувства юмора, но вот шутка: 404 — шутка не найдена.",
        "Что скажет бот, если ему скучно? 'Ping me later!'"],
    r"повтор(?:и)?\s+(.+)": lambda m: m.group(1),
    r"\bпоиск\b\s+(.+)": lambda m: search_web(m.group(1)),
    r"\bпогода\b(?:\s+в\s+)?([а-яА-ЯёЁ\s\-]*)": lambda m: (get_weather(m.group(1).strip()) if m.group(1).strip() else "city_request"),
    r"посчитай\s+([\d+\-*/().\s]+)|\bвычисли\b\s*([\d+\-*/().\s]+)|^[\d+\-*/().\s]+$": lambda m: evaluate_expression(m.group(1) or m.group(2) or m.group(0)),
    r"\bхочу\b|\bда\b|\bконечно\b": [
        "Расскажи, что случилось. Я слушаю...",
        "Как я могу тебя поддержать? 💙",
        "Я рядом, делись чем угодно.",
        "Ты не один(одна), я рядом.",
        "Доверяй, говори — я слушаю внимательно 👂"],
    r"как\s+меня\s+зовут|ты\s+помнишь\s+мо[её]\s+имя": lambda _: (f"Тебя зовут {user_name}!" if user_name else "Я пока не знаю, как тебя зовут. Как тебя зовут?"),
}

def analyze_sentiment(text):
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in positive_keywords):
        return "Ты выглядишь счастливым! 😊 Чем порадовать тебя ещё?"
    if any(keyword in text_lower for keyword in negative_keywords):
        return "Ты, кажется, расстроен... 😔 Хочешь поговорить об этом?"
    translated = translator.translate(text, dest="en").text
    polarity = TextBlob(translated).sentiment.polarity
    if polarity > 0.3:
        return "Ты излучаешь позитив! 🌟 Чем помочь?"
    elif polarity < -0.3:
        return "Вижу, тебе тяжело... Могу чем-то помочь?"
    else:
        return None

def get_response(message):
    global waiting_for_city, user_name, waiting_for_talk
    message = message.strip()
    if waiting_for_city:
        waiting_for_city = False
        return get_weather(message)
    if waiting_for_talk:
        waiting_for_talk = False
        return random.choice(["Я здесь, чтобы выслушать. Что тебя беспокоит? 💬", "Ты можешь довериться мне. Расскажи, что произошло. 🤗"])
    for pattern, reply in responses.items():
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            if isinstance(reply, list):
                return random.choice(reply)
            result = reply(match)
            if result == "city_request":
                waiting_for_city = True
                return "В каком городе проверить погоду?"
            return result
    sentiment_response = analyze_sentiment(message)
    if sentiment_response:
        if "расстроен" in sentiment_response:
            waiting_for_talk = True
        return sentiment_response
    return random.choice([
        "Расскажи, о чём ты думаешь? 🤔",
        "Чем могу тебя порадовать? 😊"])

def get_weather(city):
    try:
        city = city.strip()
        city_en = translator.translate(city, dest="en").text
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_en}&appid={API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data["main"]["temp"]
            weather_desc = data["weather"][0]["description"]
            return f"В городе {city} сейчас {weather_desc}, температура {temp}°C."
        return "Не удалось получить погоду. Проверь название города."
    except Exception as e:
        return f"Ошибка: {e}"

def search_web(query):
    webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
    return f"Открываю результаты поиска по запросу '{query}'."

def evaluate_expression(expr):
    try:
        result = eval(expr)
        return f"Результат: {result}"
    except:
        return "Не могу вычислить это выражение."

def start_conversation():
    print("Бот: Привет! Я твой виртуальный помощник. Как тебя зовут?")
    log_message("Бот", "Привет! Я твой виртуальный помощник. Как тебя зовут?")
    global user_name
    while True:
        user_input = input("Вы: ").strip()
        log_message("Вы", user_input)
        name_match = re.search(
            r"(?:меня зовут|зовут|я)\s*([А-Яа-яЁё]+)|^([А-Яа-яЁё]+)$", 
            user_input, 
            re.IGNORECASE
        )
        if name_match:
            user_name = name_match.group(1) or name_match.group(2)
            break
        response = "Не расслышал имя. Попробуй ещё раз (например, 'Лиля')."
        print("Бот:", response)
        log_message("Бот", response)
    
    greeting = f"Приятно познакомиться, {user_name}! Задавай любой вопрос."
    print("Бот:", greeting)
    log_message("Бот", greeting)
    
    while True:
        user_input = input("Вы: ")
        log_message("Вы", user_input)
        if user_input.lower() in ["стоп", "выход"]:
            goodbye = "До новых встреч! 💫"
            print("Бот:", goodbye)
            log_message("Бот", goodbye)
            break
        response = get_response(user_input)
        print("Бот:", response)
        log_message("Бот", response)
if __name__ == "__main__":
    start_conversation()


