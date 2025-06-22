from plyer import notification
import pyttsx3

_engine = pyttsx3.init()

def send_notification(title, message):
    notification.notify(title=title, message=message, timeout=5)
    _engine.say(message)
    _engine.runAndWait()
