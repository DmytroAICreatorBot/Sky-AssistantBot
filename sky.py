import os
import subprocess
import webbrowser
import requests
import customtkinter as ctk
import pyttsx3
import speech_recognition as sr
import threading
import shutil
import queue
from datetime import datetime
import time
import re
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем путь к проекту и ключ API из переменных окружения
project_dir = os.getenv("PROJECT_DIR")
user_name_file = os.path.join(project_dir, "sky_user.txt")
history_file = os.path.join(project_dir, "sky_history.txt")

# Настройка GUI
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Инициализация speech engine
def init_speech_engine():
    eng = pyttsx3.init()
    voices = eng.getProperty('voices')
    for v in voices:
        if 'russian' in v.name.lower() or 'рус' in v.name.lower():
            eng.setProperty('voice', v.id)
            break
    eng.setProperty('rate', 160)
    eng.setProperty('volume', 1.0)
    return eng

engine = init_speech_engine()
use_voice_output = True

# Автозапуск флаг и функция
auto_start_enabled = False
auto_start_thread = None
auto_start_event = threading.Event()

def auto_start_worker():
    while not auto_start_event.is_set():
        user_input = "Привет"
        response = get_sky_response(user_input)
        output.configure(state="normal")
        output.insert("end", f"Автозапуск:\nТы: {user_input}\nSKY: {response}\n\n")
        output.see("end")
        output.configure(state="disabled")
        speak(response)
        for _ in range(30):
            if auto_start_event.is_set():
                break
            time.sleep(1)

def toggle_auto_start():
    global auto_start_enabled, auto_start_thread, auto_start_event
    if auto_start_enabled:
        # Остановить автозапуск
        auto_start_event.set()
        auto_start_thread = None
        auto_start_enabled = False
        btn_auto_start.configure(text="Включить автозапуск", fg_color="#1f6aa5")
        output.configure(state="normal")
        output.insert("end", "Автозапуск выключен.\n\n")
        output.configure(state="disabled")
        speak("Автозапуск выключен.")
    else:
        # Запустить автозапуск
        auto_start_event.clear()
        auto_start_thread = threading.Thread(target=auto_start_worker, daemon=True)
        auto_start_thread.start()
        auto_start_enabled = True
        btn_auto_start.configure(text="Выключить автозапуск", fg_color="#3b8ed0")
        output.configure(state="normal")
        output.insert("end", "Автозапуск включен.\n\n")
        output.configure(state="disabled")
        speak("Автозапуск включен.")

# Очередь и поток для озвучки (TTS)
tts_queue = queue.Queue()

def tts_worker():
    while True:
        text = tts_queue.get()
        if text is None:
            break
        engine.say(text)
        engine.runAndWait()
        tts_queue.task_done()

threading.Thread(target=tts_worker, daemon=True).start()

def speak(text):
    if use_voice_output:
        tts_queue.put(text)

def get_user_name():
    if os.path.exists(user_name_file):
        return open(user_name_file, "r", encoding="utf-8").read().strip()
    else:
        name = "Друг"
        open(user_name_file, "w", encoding="utf-8").write(name)
        return name

MAX_HISTORY_DISPLAY = 30

def append_to_history(user, assistant):
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(f"Ты: {user}\nSKY: {assistant}\n\n")

def get_history():
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return ''.join(lines[-MAX_HISTORY_DISPLAY*2:])
    return "История пуста."

def clear_history():
    open(history_file, "w", encoding="utf-8").close()

API_KEY = os.getenv("API_KEY")

chat_history = [
    {"role": "system", "content": "Ты голосовой ассистент по имени SKY. Ты дружелюбный, умный и говоришь по-русски. Обращайся к пользователю по имени."}
]

def get_openrouter_response(prompt):
    chat_history.append({"role": "user", "content": prompt})
    url = "https://openrouter.ai/api/v1/chat/completions"
    resp = requests.post(url, headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }, json={"model": "meta-llama/llama-3-8b", "messages": chat_history})
    if resp.status_code == 200:
        answer = resp.json()["choices"][0]["message"]["content"]
        chat_history.append({"role": "assistant", "content": answer})
        return answer
    return f"Ошибка API: {resp.status_code}"

def clear_memory():
    global chat_history
    chat_history = [
        {"role": "system", "content": "Ты голосовой ассистент по имени SKY. Ты дружелюбный, умный и говоришь по-русски. Обращайся к пользователю по имени."}
    ]
    output.configure(state="normal")
    output.insert("end", "🧠 Память очищена.\n\n")
    output.configure(state="disabled")
    speak("Память очищена.")

def get_sky_response(user_input):
    ui = user_input.lower()
    name = get_user_name()
    resp = ""
    try:
        if "привет" in ui:
            resp = f"Привет, {name}! Я SKY."
        elif "время" in ui:
            resp = f"{name}, сейчас {datetime.now().strftime('%H:%M')}."
        elif "как дела" in ui:
            resp = f"У меня всё отлично, {name}! А у тебя?"
        elif "открой браузер" in ui:
            subprocess.Popen(os.getenv("BROWSER_PATH"))
            resp = "Открываю браузер."
        elif "создай папку" in ui:
            fn = ui.split("создай папку")[-1].strip()
            os.makedirs(fn, exist_ok=True)
            resp = f"Папка '{fn}' создана."
        elif "создай файл" in ui:
            fn = ui.split("создай файл")[-1].strip()
            open(fn, 'w', encoding="utf-8").close()
            resp = f"Файл '{fn}' создан."
        elif "открой файл" in ui or "открой папку" in ui:
            path = ui.split("открой файл")[-1].strip() if "открой файл" in ui else ui.split("открой папку")[-1].strip()
            os.startfile(path)
            resp = f"Открываю '{path}'."
        elif "удали файл" in ui or "удали папку" in ui:
            path = ui.split("удали файл")[-1].strip() if "удали файл" in ui else ui.split("удали папку")[-1].strip()
            if os.path.isfile(path):
                os.remove(path)
                resp = f"Файл '{path}' удалён."
            elif os.path.isdir(path):
                shutil.rmtree(path)
                resp = f"Папка '{path}' удалена."
            else:
                resp = f"Путь '{path}' не найден."
        elif "запусти музыку" in ui:
            subprocess.Popen(os.getenv("MUSIC_PATH"))
            resp = "Запускаю музыку."
        elif "останови музыку" in ui:
            subprocess.run(["taskkill","/IM","Spotify.exe","/F"])
            resp = "Останавливаю музыку."
        elif "найди в интернете" in ui:
            q = ui.split("найди в интернете")[-1].strip()
            webbrowser.open(f"https://www.google.com/search?q={q.replace(' ', '+')}")
            resp = f"Ищу: {q}"
        elif "погода в" in ui:
            city = ui.split("погода в")[-1].strip()
            geo = requests.get("https://nominatim.openstreetmap.org/search", params={"q":city,"format":"json","limit":1}, headers={"User-Agent":"SKY"})
            if not geo.json():
                resp = f"Не нашёл город '{city}'."
            else:
                lat, lon = geo.json()[0]["lat"], geo.json()[0]["lon"]
                w = requests.get("https://api.open-meteo.com/v1/forecast", params={"latitude":lat,"longitude":lon,"current_weather":"true"}).json()["current_weather"]
                resp = f"{name}, в {city}: {w['temperature']}°C, ветер {w['windspeed']} км/ч."
        elif "переключи режим" in ui:
            global use_voice_output
            use_voice_output = not use_voice_output
            resp = "Озвучка " + ("включена" if use_voice_output else "выключена")
        elif "покажи историю" in ui:
            resp = get_history()
        elif "очисти историю" in ui:
            clear_history()
            resp = "История очищена."
        elif "таймер" in ui:
            seconds = 0
            match = re.search(r'(\d+)\s*(секунд|сек|минут|мин|час)', ui)
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                if unit.startswith("сек"):
                    seconds = value
                elif unit.startswith("мин"):
                    seconds = value * 60
                elif unit.startswith("час"):
                    seconds = value * 3600
            if seconds > 0:
                resp = f"Запускаю таймер на {value} {unit}."
                threading.Thread(target=timer_thread, args=(seconds,), daemon=True).start()
            else:
                resp = "Не понял время таймера."
        elif ui.strip() == "очисти память":
            clear_memory()
            resp = "Память очищена."
        else:
            resp = get_openrouter_response(user_input)
    except Exception as e:
        resp = f"Ошибка обработки команды: {e}"
    append_to_history(user_input, resp)
    return resp

def timer_thread(seconds):
    time.sleep(seconds)
    output.configure(state="normal")
    output.insert("end", f"⏰ Таймер на {seconds} секунд завершён!\n\n")
    output.see("end")
    output.configure(state="disabled")
    speak(f"Таймер на {seconds} секунд завершён!")

def recognize_speech_from_mic(recognizer, microphone):
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, phrase_time_limit=5)
    try:
        return recognizer.recognize_google(audio, language="ru-RU")
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""

# Горячее слово
def hotword_listener():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    while True:
        print("Слушаю горячее слово...")
        text = recognize_speech_from_mic(recognizer, mic).lower()
        if "sky" in text:
            output.configure(state="normal")
            output.insert("end", "🔔 Горячее слово распознано. Говорите команду...\n")
            output.see("end")
            output.configure(state="disabled")
            speak("Слушаю команду")
            cmd = recognize_speech_from_mic(recognizer, mic)
            if cmd:
                output.configure(state="normal")
                output.insert("end", f"Ты: {cmd}\n")
                output.configure(state="disabled")
                resp = get_sky_response(cmd)
                output.configure(state="normal")
                output.insert("end", f"SKY: {resp}\n\n")
                output.see("end")
                output.configure(state="disabled")
                speak(resp)

# GUI
root = ctk.CTk()
root.title("SKY Assistant")
root.geometry("700x550")

frame = ctk.CTkFrame(root)
frame.pack(padx=10, pady=10, fill="both", expand=True)

output = ctk.CTkTextbox(frame, state="disabled", width=680, height=400)
output.pack(padx=10, pady=10, fill="both", expand=True)

entry = ctk.CTkEntry(frame, width=600)
entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)

def on_send():
    user_text = entry.get().strip()
    if not user_text:
        return
    output.configure(state="normal")
    output.insert("end", f"Ты: {user_text}\n")
    output.configure(state="disabled")
    entry.delete(0, "end")
    threading.Thread(target=process_input, args=(user_text,), daemon=True).start()

def process_input(text):
    resp = get_sky_response(text)
    output.configure(state="normal")
    output.insert("end", f"SKY: {resp}\n\n")
    output.see("end")
    output.configure(state="disabled")
    speak(resp)

send_button = ctk.CTkButton(frame, text="Отправить", command=on_send)
send_button.pack(side="right", padx=10, pady=10)

btn_auto_start = ctk.CTkButton(root, text="Включить автозапуск", command=toggle_auto_start, fg_color="#1f6aa5")
btn_auto_start.pack(pady=5)

threading.Thread(target=hotword_listener, daemon=True).start()

root.mainloop()

# Корректное завершение потоков при закрытии приложения
tts_queue.put(None)
auto_start_event.set()
