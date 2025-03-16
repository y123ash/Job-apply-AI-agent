#!/bin/bash

# Job Application AI Agent Installation Script

echo "Installing Job Application AI Agent..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$python_version < 3.8" | bc) -eq 1 ]]; then
    echo "Python version $python_version is not supported. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install spaCy model
echo "Installing spaCy model..."
python -m spacy download en_core_web_sm

# Install the package in development mode
echo "Installing the package..."
pip install -e .

echo "Installation complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"
echo "To start the web interface, run: job-apply-ai web"
echo "To see all available commands, run: job-apply-ai --help" 