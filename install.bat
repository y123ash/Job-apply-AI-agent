@echo off
echo Installing Job Application AI Agent...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYVER=%%I
for /f "tokens=1,2 delims=." %%I in ("%PYVER%") do (
    set PYMAJOR=%%I
    set PYMINOR=%%J
)

if %PYMAJOR% lss 3 (
    echo Python version %PYVER% is not supported. Please install Python 3.8 or higher.
    exit /b 1
)

if %PYMAJOR%==3 (
    if %PYMINOR% lss 8 (
        echo Python version %PYVER% is not supported. Please install Python 3.8 or higher.
        exit /b 1
    )
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Install spaCy model
echo Installing spaCy model...
python -m spacy download en_core_web_sm

REM Install the package in development mode
echo Installing the package...
pip install -e .

echo Installation complete!
echo To activate the virtual environment, run: venv\Scripts\activate.bat
echo To start the web interface, run: job-apply-ai web
echo To see all available commands, run: job-apply-ai --help

pause 