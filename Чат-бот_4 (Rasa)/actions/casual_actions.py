from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from transformers import pipeline
from typing import Any, Text, Dict, List

sentiment_analyzer = pipeline("sentiment-analysis", model="blanchefort/rubert-base-cased-sentiment")

class ActionAnalyzeMood(Action):
    def name(self) -> Text:
        return "action_analyze_mood"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lang = domain.get("config", {}).get("language", "ru")
        text = tracker.latest_message.get("text")

        mood_keywords = ["настроение", "как ты", "как дела", "что с настроением"] if lang == "ru" else ["mood", "how are you"]
        if not any(keyword in text.lower() for keyword in mood_keywords):
            return []

        result = sentiment_analyzer(text)[0]
        mood = result['label']
        score = round(result['score'], 2)

        if lang == "ru":
            msg = {
                "POSITIVE": f"Ты в хорошем настроении! 😊 (уверенность: {score})",
                "NEGATIVE": f"Похоже, тебе грустно. 😔 (уверенность: {score})"
            }.get(mood, f"Настроение нейтральное. 🤔 (уверенность: {score})")
        else:
            msg = {
                "POSITIVE": f"You're in a good mood! 😊 (confidence: {score})",
                "NEGATIVE": f"Seems like you're sad. 😔 (confidence: {score})"
            }.get(mood, f"Neutral mood. 🤔 (confidence: {score})")

        dispatcher.utter_message(text=msg)
        return [SlotSet("last_bot_message", msg)]

class ActionTalkSupport(Action):
    def name(self) -> Text:
        return "action_talk_support"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lang = domain.get("config", {}).get("language", "ru")
        user_name = tracker.get_slot("name") or ("друг" if lang == "ru" else "friend")

        message = f"{user_name}, я вас слушаю. Что случилось?" if lang == "ru" else f"{user_name}, I'm here to help. What happened?"
        dispatcher.utter_message(text=message)
        return [SlotSet("last_bot_message", message)]
