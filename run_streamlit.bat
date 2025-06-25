@echo off
echo [INFO] Lancement de Streamlit avec l'environnement virtuel...
set MAPBOX_API_KEY=pk.eyJ1IjoibGFwcm9kaWdlIiwiYSI6ImNtY2Nkb3B5eDA1czIyanMzdWhqaHFkaG0ifQ.428XIl4tG2sA08BiFuePQQ
for /f "delims=" %%i in ('python -c "import sys; print(sys.executable)"') do (
    set PYEXEC=%%i
)
"%PYEXEC%" -m streamlit run streamlit_app/app.py
pause
