@echo off
rem Gera dist\Meerkat.exe (requer Python 3.12+: winget install Python.Python.3.12)
cd /d "%~dp0"
py -3 -m venv .venv || goto :error
.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt || goto :error
.venv\Scripts\pytest -q || goto :error
.venv\Scripts\pyinstaller --noconfirm --clean meerkat.spec || goto :error
echo.
echo Pronto: %cd%\dist\Meerkat.exe
pause
exit /b 0
:error
echo.
echo Falhou. Veja a mensagem acima.
pause
exit /b 1
