
*(If PyAudio gives error, users can install system version.)*

---

# ✅ 4. alexa.py (Core Code)  
Paste this:

```python
import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser

engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)

    try:
        print("Recognizing...")
        command = r.recognize_google(audio, language="en-in")
        print("User said:", command)
    except:
        return ""
    return command.lower()

speak("Hello, I am Alexa. How can I help you?")

while True:
    cmd = listen()

    if "time" in cmd:
        time = datetime.datetime.now().strftime("%H:%M")
        speak(f"The time is {time}")

    elif "date" in cmd:
        date = datetime.datetime.now().strftime("%d %B %Y")
        speak(f"Today's date is {date}")

    elif "search" in cmd:
        query = cmd.replace("search", "")
        webbrowser.open(f"https://www.google.com/search?q={query}")
        speak("Searching Google")

    elif "open youtube" in cmd:
        speak("Opening YouTube")
        webbrowser.open("https://youtube.com")

    elif "exit" in cmd or "stop" in cmd:
        speak("Goodbye")
        break

