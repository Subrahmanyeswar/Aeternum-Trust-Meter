@echo off
cd /d %~dp0
echo [1/3] Activating virtual environment...
if not exist .venv (
    echo [.venv not found, creating...]
    python -m venv .venv
)
call .venv\Scripts\activate
echo [2/3] Installing/Updating dependencies...
pip install -r requirements.txt
echo [3/3] Starting Aeternum API on port 8000...
uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
