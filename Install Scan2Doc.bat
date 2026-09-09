@echo off
setlocal
cd /d "%~dp0"
set "PY_CMD="
where py >nul 2>nul
if not errorlevel 1 (
  for %%V in (3.13 3.12 3.11 3.10) do (
    py -%%V -c "import sys" >nul 2>nul
    if not errorlevel 1 if not defined PY_CMD set "PY_CMD=py -%%V"
  )
)
if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)" >nul 2>nul
    if not errorlevel 1 set "PY_CMD=python"
  )
)
if not defined PY_CMD goto :no_python
echo Using:
%PY_CMD% --version
%PY_CMD% -m venv .venv
if errorlevel 1 goto :error
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip setuptools==84.0.0
if errorlevel 1 goto :error
python -m pip install -r requirements.txt
if errorlevel 1 goto :error
echo.
echo Installation complete. Double-click Start Scan2Doc.bat.
pause
exit /b 0
:no_python
echo.
echo No supported 64-bit Python was found. Install Python 3.10, 3.11, 3.12, or 3.13.
echo Installed Python versions reported by the launcher:
py -0p 2>nul
pause
exit /b 1
:error
echo.
echo Installation failed. See the messages above. Python 3.10-3.13 64-bit is supported.
pause
exit /b 1
