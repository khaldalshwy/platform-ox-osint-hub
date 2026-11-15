@echo off
set PYTHONIOENCODING=utf-8
echo =====================================================
echo    Starting OSINT Platform OX
echo =====================================================
python 04_orchestration\pipeline_runner.py
echo.
echo [*] Launching Streamlit Operations Center on http://localhost:8501 ...
python -m streamlit run 06_presentation\streamlit_app\app.py --browser.gatherUsageStats false
pause
