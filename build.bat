@echo off
chcp 65001 > nul
echo ====================================================
echo  Iniciando compilação do File Organizer (.exe)
echo ====================================================

python -m pip install -r requirements.txt pyinstaller
python build.py

pause
