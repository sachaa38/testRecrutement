@echo off
REM Installer les dépendances la première fois seulement
python-portable\python.exe -m pip install --upgrade pip
python-portable\python.exe -m pip install streamlit PyPDF2 python-docx pandas openai

REM Lancer l'application
python-portable\python.exe -m streamlit run testRecrutement.py
pause
