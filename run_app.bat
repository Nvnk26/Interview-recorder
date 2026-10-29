@echo off
cd /d "%~dp0"
if not exist ".venv312\Scripts\python.exe" (
    echo Khong tim thay moi truong .venv312.
    echo Hay tao moi truong va cai thu vien theo huong dan truoc.
    pause
    exit /b 1
)
"%~dp0.venv312\Scripts\python.exe" -m streamlit run "%~dp0app.py"
pause
