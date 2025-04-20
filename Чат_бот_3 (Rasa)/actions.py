import requests
import datetime
import spacy
import pymorphy2
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import FormValidationAction
from rasa_sdk.events import SlotSet
from transformers import pipeline
from pymorphy2 import MorphAnalyzer
import re
import ast
from typing import Any, Text, Dict, List

# Инициализация NLP-моделей
nlp = spacy.load("ru_core_news_md")
morph = MorphAnalyzer()
sentiment_analyzer = pipeline("sentiment-analysis", model="blanchefort/rubert-base-cased-sentiment")

class ActionTellTime(Action):
    def name(self) -> Text:
        return "action_tell_time"

    def run(self, dispatcher: CollectingDispatcher, 
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            
        time_format = domain.get("config", {}).get("time_format", "%H:%M")
        now = datetime.datetime.now().strftime(time_format)
        message = f"Сейчас {now}"
        dispatcher.utter_message(text=message)
        return [SlotSet("last_bot_message", message)]

class ActionTellDate(Action):
    def name(self) -> Text:
        return "action_tell_date"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = domain.get("config", {}).get("language", "ru")
        date_format = "%d.%m.%Y" if lang == "ru" else "%Y-%m-%d"
        date = datetime.datetime.now().strftime(date_format)
        message = f"Сегодня {date}"
        dispatcher.utter_message(text=message)
        return [SlotSet("last_bot_message", message)]

class ActionTellDay(Action):
    def name(self) -> Text:
        return "action_tell_day"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = domain.get("config", {}).get("language", "ru")
        day = datetime.datetime.now().strftime("%A")
        
        days_translation = {
            "ru": {
                "Monday": "Понедельник",
                "Tuesday": "Вторник",
                "Wednesday": "Среда",
                "Thursday": "Четверг",
                "Friday": "Пятница",
                "Saturday": "Суббота",
                "Sunday": "Воскресенье"
            },
            "en": {
                "Monday": "Monday",
                "Tuesday": "Tuesday",
                "Wednesday": "Wednesday",
                "Thursday": "Thursday",
                "Friday": "Friday",
                "Saturday": "Saturday",
                "Sunday": "Sunday"
            }
        }
        
        day_localized = days_translation.get(lang, {}).get(day, day)
        message = f"Сегодня {day_localized}"
        dispatcher.utter_message(text=message)
        return [SlotSet("last_bot_message", message)]

class ActionGetWeather(Action):
    def name(self) -> Text:
        return "action_get_weather"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = domain.get("config", {}).get("language", "ru")
        city = tracker.get_slot("city")
        
        # Извлечение города из сообщения
        if not city:
            text = tracker.latest_message.get("text")
            doc = nlp(text)
            city = next((ent.text for ent in doc.ents if ent.label_ == "GPE"), None)

        # Нормализация названия города
        if city:
            parsed_city = morph.parse(city)[0]
            city_norm = parsed_city.normal_form
        else:
            city_norm = None

        if not city_norm:
            dispatcher.utter_message(response="utter_ask_city")
            return []

        # Запрос к API погоды
        api_key = "22b6c1843b73184829f5eec1bb60c502"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_norm}&appid={api_key}&units=metric&lang={lang}"
        
        try:
            response = requests.get(url)
            data = response.json()
            if data.get("cod") == 200:
                temp = data["main"]["temp"]
                desc = data["weather"][0]["description"]
                message = f"В городе {city_norm} сейчас {desc}, температура {temp}°C." if lang == "ru" else f"In {city_norm}: {desc}, {temp}°C."
            else:
                message = f"Не удалось найти погоду для {city_norm}." if lang == "ru" else f"Weather for {city_norm} not found."
        except Exception as e:
            message = f"Ошибка получения погоды: {str(e)}" if lang == "ru" else f"Weather error: {str(e)}"
        
        dispatcher.utter_message(text=message)
        return [SlotSet("city", city_norm), SlotSet("last_bot_message", message)]
    
        
class ActionRememberName(Action):
    def name(self) -> Text:
        return "action_remember_name"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = domain.get("config", {}).get("language", "ru")
        text = tracker.latest_message.get("text")
        doc = nlp(text)
        name = next((ent.text for ent in doc.ents if ent.label_ == "PER"), None)

        if not name:
            dispatcher.utter_message(response="utter_ask_name")
            return []

        message = f"Приятно познакомиться, {name}!" if lang == "ru" else f"Nice to meet you, {name}!"
        dispatcher.utter_message(text=message)
        return [SlotSet("name", name), SlotSet("last_bot_message", message)]

class ActionGetName(Action):
    def name(self) -> Text:
        return "action_get_name"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = domain.get("config", {}).get("language", "ru")
        name = tracker.get_slot("name")
        
        if name:
            message = f"Тебя зовут {name}, верно?" if lang == "ru" else f"Your name is {name}, right?"
        else:
            message = "Я пока не знаю, как тебя зовут." if lang == "ru" else "I don't know your name yet."
            
        dispatcher.utter_message(text=message)
        return [SlotSet("last_bot_message", message)]

class ActionAnalyzeMood(Action):
    def name(self) -> Text:
        return "action_analyze_mood"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = domain.get("config", {}).get("language", "ru")
        text = tracker.latest_message.get("text")
        
        mood_keywords = ["настроение", "как ты", "как дела", "что с настроением"] if lang == "ru" else ["mood", "how are you"]
        
        if not any(keyword in text.lower() for keyword in mood_keywords):
            return []
            
        result = sentiment_analyzer(text)[0]
        mood = result['label']
        score = round(result['score'], 2)
        
        if lang == "ru":
            if mood == "POSITIVE":
                msg = f"Ты в хорошем настроении! 😊 (уверенность: {score})"
            elif mood == "NEGATIVE":
                msg = f"Похоже, тебе грустно. 😔 (уверенность: {score})"
            else:
                msg = f"Настроение нейтральное. 🤔 (уверенность: {score})"
        else:
            if mood == "POSITIVE":
                msg = f"You're in a good mood! 😊 (confidence: {score})"
            elif mood == "NEGATIVE":
                msg = f"Seems like you're sad. 😔 (confidence: {score})"
            else:
                msg = f"Neutral mood. 🤔 (confidence: {score})"
            
        dispatcher.utter_message(text=msg)
        return [SlotSet("last_bot_message", msg)]

class ActionTalkSupport(Action):
    def name(self) -> Text:
        return "action_talk_support"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = domain.get("config", {}).get("language", "ru")
        user_name = tracker.get_slot("name") or ("друг" if lang == "ru" else "friend")
        
        message = (
            f"{user_name}, я вас слушаю. Что случилось?" 
            if lang == "ru" 
            else f"{user_name}, I'm here to help. What happened?"
        )
        
        dispatcher.utter_message(text=message)
        return [SlotSet("last_bot_message", message)]

class ActionSearchWeb(Action):
    def name(self) -> Text:
        return "action_search_web"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = domain.get("config", {}).get("language", "ru")
        
        # Попробуем получить слот
        query = tracker.get_slot("query")

        # Если слот пустой, пытаемся извлечь запрос прямо из текста
        if not query:
            query = tracker.latest_message.get("text")
            if not query:
                msg = "Что именно вы хотите найти?" if lang == "ru" else "What exactly do you want to search for?"
                dispatcher.utter_message(text=msg)
                return [SlotSet("last_bot_message", msg)]
        
        # Создаем ссылку на Google
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        message = f"Вот что я нашел: {search_url}" if lang == "ru" else f"Here's what I found: {search_url}"
        
        dispatcher.utter_message(text=message)

        # Заполняем слот query с полным текстом запроса
        return [SlotSet("query", query), SlotSet("last_bot_message", message)]


class ActionCalculate(Action):
    def name(self) -> Text:
        return "action_calculate"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = domain.get("config", {}).get("language", "ru")
        text = tracker.latest_message.get("text")
        expression = re.findall(r"[0-9+\-*/().]+", text)
        
        if expression:
            try:
                result = self.safe_eval(expression[0])
                message = f"Результат: {result}" if lang == "ru" else f"Result: {result}"
            except Exception as e:
                message = "Не могу посчитать. Убедись, что выражение корректное." if lang == "ru" else "Can't calculate. Please check the expression."
        else:
            message = "Я не нашёл выражение для подсчёта." if lang == "ru" else "No expression found to calculate."
            
        dispatcher.utter_message(text=message)
        return [SlotSet("last_bot_message", message)]

    def safe_eval(self, expression: Text) -> float:
        parsed = ast.parse(expression, mode='eval')
        allowed_nodes = (ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div)
        
        for node in ast.walk(parsed):
            if not isinstance(node, allowed_nodes):
                raise ValueError("Недопустимая операция")
                
        return eval(expression)

class ActionRepeatPhrase(Action):
    def name(self) -> Text:
        return "action_repeat_phrase"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = domain.get("config", {}).get("language", "ru")
        phrase = next(tracker.get_latest_entity_values("repeat_phrase"), None)
        
        if phrase:
            dispatcher.utter_message(text=phrase)
            return [SlotSet("last_bot_message", phrase)]
        
        error_msg = "Мне нечего повторить." if lang == "ru" else "Nothing to repeat."
        dispatcher.utter_message(text=error_msg)
        return [SlotSet("last_bot_message", error_msg)]