@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found in PATH.
    pause
    exit /b 1
)

where pandoc >nul 2>nul
if errorlevel 1 (
    echo Pandoc was not found in PATH.
    pause
    exit /b 1
)

python "%~dp0convert_word_to_html.py"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Conversion failed with exit code %EXIT_CODE%.
    pause
    exit /b %EXIT_CODE%
)

echo.
echo Conversion completed. Open out_html\index.html to browse the result.
pause
