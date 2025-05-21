import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import spacy
import pymorphy2
from pymorphy2 import MorphAnalyzer
from typing import Any, Text, Dict, List

morph = pymorphy2.MorphAnalyzer()
nlp = spacy.load("ru_core_news_md")

class ActionGetWeather(Action):
    def name(self) -> Text:
        return "action_get_weather"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lang = domain.get("config", {}).get("language", "ru")
        city = tracker.get_slot("city")

        if not city:
            text = tracker.latest_message.get("text")
            doc = nlp(text)
            city = next((ent.text for ent in doc.ents if ent.label_ == "GPE"), None)

        city_norm = morph.parse(city)[0].normal_form if city else None

        if not city_norm:
            dispatcher.utter_message(response="utter_ask_city")
            return []

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
