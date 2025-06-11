# SKY Assistant

🎙️ **SKY Assistant** — це голосовий асистент для ПК з інтерфейсом на Python (CustomTkinter), який виконує команди користувача через мову.

## 🧠 Можливості

- Розпізнавання голосу через гаряче слово  
- Голосова відповідь (TTS)  
- Запуск додатків  
- Пошук інформації онлайн  
- Прогноз погоди  
- Робота з файлами  
- Таймери  
- Інтеграція з OpenRouter API (штучний інтелект)  

## 🛠️ Технології

- Python  
- CustomTkinter  
- SpeechRecognition / pyttsx3  
- OpenRouter API  
- Weather API  

## 🧩 Структура проєкту

sky-assistant/  
│  
├── main.py # головний файл запуску  
├── voice/ # робота з голосом  
├── core/ # логіка асистента  
├── utils/ # утиліти, обробка часу, дані  
├── gui/ # CustomTkinter інтерфейс  
├── assets/ # ресурси (іконки, фон)  
└── README.md # цей файл

## 🔧 Установка

1. Встановіть Python 3.9 або вище: [python.org](https://www.python.org/downloads/)
2. Клонуйте репозиторій або скачайте архів
3. Встановіть залежності:
```bash
pip install -r requirements.txt 

## 🚀 Запуск

```bash
python main.py
