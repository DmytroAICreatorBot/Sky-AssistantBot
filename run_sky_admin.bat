@echo off
:: Проверяем, запущен ли скрипт с правами администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Запуск от имени администратора...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:: Если права администратора есть — переходим в папку и запускаем Python скрипт
cd /d "C:\Users\dimap\Sky-assistant"
python sky.py

pause
