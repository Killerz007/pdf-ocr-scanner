@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run Install Scan2Doc.bat first.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
python -m pip install pip-audit==2.10.1
if errorlevel 1 goto :error
python -m pip_audit -r requirements.txt
pause
exit /b %errorlevel%
:error
echo Security audit setup failed.
pause
exit /b 1
