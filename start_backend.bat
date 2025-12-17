@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Starts the DS-STAR backend on http://127.0.0.1:8000
REM Use this if you are running the frontend separately (e.g. `npm run dev`).

pushd "%~dp0"

REM If port 8000 is already in use, bail with a clear message.
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo Port 8000 is already in use.
  echo - Stop the existing process or run `start_application.bat` to auto-pick ports.
  popd
  endlocal
  exit /b 1
)

echo Starting DS-STAR backend on http://127.0.0.1:8000 ...
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000

popd
endlocal
