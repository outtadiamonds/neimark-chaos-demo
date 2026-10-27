@echo off
rem Сборка двойным щелчком. Аргументы передаются в tools\build.py, например: build.bat all --check
chcp 65001 >nul
cd /d "%~dp0"
".venv\Scripts\python.exe" tools\build.py %*
pause
