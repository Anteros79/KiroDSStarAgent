@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Starts backend + frontend on the next available ports and opens the browser to the frontend URL.
REM - Backend: FastAPI (uvicorn) on 127.0.0.1
REM - Frontend: Vite dev server (React) with proxy to backend (/api, /ws)
REM
REM Requirements:
REM - Python available on PATH (or `py` launcher)
REM - Node/npm installed
REM - `npm install` already run in `frontend/`

pushd "%~dp0"

call :find_free_port 8000 BACKEND_PORT
call :find_free_port 3000 FRONTEND_PORT

echo.
echo Using ports:
echo   Backend  : http://127.0.0.1:%BACKEND_PORT%
echo   Frontend : http://127.0.0.1:%FRONTEND_PORT%
echo.

REM Start backend in a new window
set "BACKEND_CMD=python -m uvicorn src.api.server:app --host 127.0.0.1 --port %BACKEND_PORT%"
start "DS-STAR Backend" cmd /k "%BACKEND_CMD%"

REM Start frontend in a new window, wiring proxy to the chosen backend port.
REM Use `start ... /D` to avoid nested-quote path issues (common cause of:
REM "The filename, directory name, or volume label syntax is incorrect.")
set "FRONTEND_DIR=%CD%\frontend"
if not exist "%FRONTEND_DIR%" (
  echo Frontend directory not found: %FRONTEND_DIR%
) else (
  start "DS-STAR Frontend" /D "%FRONTEND_DIR%" cmd /k "set VITE_BACKEND_PORT=%BACKEND_PORT% && set VITE_DEV_PORT=%FRONTEND_PORT% && npm run dev -- --host 127.0.0.1 --port %FRONTEND_PORT% --strictPort"
)

REM Open the browser to the chosen frontend URL
set "APP_URL=http://127.0.0.1:%FRONTEND_PORT%/"
echo Opening %APP_URL%
start "" "%APP_URL%"

popd
endlocal
exit /b 0

REM ------------------------------------------------------------
REM Finds the next available TCP port >= %1 and assigns it to var %2
REM ------------------------------------------------------------
:find_free_port
set "P=%~1"
:find_free_port_loop
REM If anything is listening on this port, bump and retry
netstat -ano | findstr /R /C:":%P% .*LISTENING" >nul 2>&1
if not errorlevel 1 (
  set /a P=P+1
  goto :find_free_port_loop
)
set "%~2=%P%"
exit /b 0

