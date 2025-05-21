from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import datetime
from typing import Any, Text, Dict, List

class ActionTellTime(Action):
    def name(self) -> Text:
        return "action_tell_time"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        time_format = domain.get("config", {}).get("time_format", "%H:%M")
        now = datetime.datetime.now().strftime(time_format)
        message = f"Сейчас {now}"
        dispatcher.utter_message(text=message)
        return [SlotSet("last_bot_message", message)]

class ActionTellDate(Action):
    def name(self) -> Text:
        return "action_tell_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lang = domain.get("config", {}).get("language", "ru")
        date_format = "%d.%m.%Y" if lang == "ru" else "%Y-%m-%d"
        date = datetime.datetime.now().strftime(date_format)
        message = f"Сегодня {date}"
        dispatcher.utter_message(text=message)
        return [SlotSet("last_bot_message", message)]

class ActionTellDay(Action):
    def name(self) -> Text:
        return "action_tell_day"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lang = domain.get("config", {}).get("language", "ru")
        day = datetime.datetime.now().strftime("%A")
        days_translation = {
            "ru": {
                "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
                "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
            },
            "en": {
                "Monday": "Monday", "Tuesday": "Tuesday", "Wednesday": "Wednesday",
                "Thursday": "Thursday", "Friday": "Friday", "Saturday": "Saturday", "Sunday": "Sunday"
            }
        }
        day_localized = days_translation.get(lang, {}).get(day, day)
        message = f"Сегодня {day_localized}"
        dispatcher.utter_message(text=message)
        return [SlotSet("last_bot_message", message)]
