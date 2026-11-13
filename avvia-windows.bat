@echo off
rem Avvia la Regia su Windows: server locale + pagina nel browser.
cd /d "%~dp0"
start "" http://127.0.0.1:8765
py -3 "%~dp0plancia\server.py" 8765
pause
