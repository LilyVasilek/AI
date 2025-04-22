from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from typing import Any, Text, Dict, List
import re, ast

class ActionSearchWeb(Action):
    def name(self) -> Text:
        return "action_search_web"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lang = domain.get("config", {}).get("language", "ru")
        query = tracker.get_slot("query") or tracker.latest_message.get("text")
        if not query:
            msg = "Что именно вы хотите найти?" if lang == "ru" else "What exactly do you want to search for?"
            dispatcher.utter_message(text=msg)
            return [SlotSet("last_bot_message", msg)]

        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        message = f"Вот что я нашел: {search_url}" if lang == "ru" else f"Here's what I found: {search_url}"
        dispatcher.utter_message(text=message)
        return [SlotSet("query", query), SlotSet("last_bot_message", message)]

class ActionCalculate(Action):
    def name(self) -> Text:
        return "action_calculate"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lang = domain.get("config", {}).get("language", "ru")
        text = tracker.latest_message.get("text")
        expression = re.findall(r"[0-9+\-*/().]+", text)

        if expression:
            try:
                result = self.safe_eval(expression[0])
                message = f"Результат: {result}" if lang == "ru" else f"Result: {result}"
            except Exception:
                message = "Не могу посчитать. Убедись, что выражение корректное." if lang == "ru" else "Can't calculate. Please check the expression."
        else:
            message = "Я не нашёл выражение для подсчёта." if lang == "ru" else "No expression found to calculate."

        dispatcher.utter_message(text=message)
        return [SlotSet("last_bot_message", message)]

    def safe_eval(self, expression: Text) -> float:
        parsed = ast.parse(expression, mode='eval')
        allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Add, ast.Sub, ast.Mult, ast.Div)
        if all(isinstance(node, allowed) for node in ast.walk(parsed)):
            return eval(expression)
        raise ValueError("Invalid expression")

class ActionRepeatPhrase(Action):
    def name(self) -> Text:
        return "action_repeat_phrase"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lang = domain.get("config", {}).get("language", "ru")
        phrase = next(tracker.get_latest_entity_values("repeat_phrase"), None)
        if phrase:
            dispatcher.utter_message(text=phrase)
            return [SlotSet("last_bot_message", phrase)]

        error_msg = "Мне нечего повторить." if lang == "ru" else "Nothing to repeat."
        dispatcher.utter_message(text=error_msg)
        return [SlotSet("last_bot_message", error_msg)]
