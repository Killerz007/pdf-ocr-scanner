@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Scan2Doc is not installed yet. Run Install Scan2Doc.bat first.
  pause
  exit /b 1
)
if "%~1"=="" (
  start "Scan2Doc" ".venv\Scripts\pythonw.exe" "%~dp0scan2doc.py"
) else (
  start "Scan2Doc" ".venv\Scripts\pythonw.exe" "%~dp0scan2doc.py" "%~1"
)
