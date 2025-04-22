from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import spacy
from typing import Any, Text, Dict, List

nlp = spacy.load("ru_core_news_md")

class ActionRememberName(Action):
    def name(self) -> Text:
        return "action_remember_name"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
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

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lang = domain.get("config", {}).get("language", "ru")
        name = tracker.get_slot("name")
        message = f"Тебя зовут {name}, верно?" if name and lang == "ru" else f"Your name is {name}, right?" if name else "Я пока не знаю, как тебя зовут." if lang == "ru" else "I don't know your name yet."

        dispatcher.utter_message(text=message)
        return [SlotSet("last_bot_message", message)]
