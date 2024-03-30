#!/bin/sh
set -e

echo "Starting installation of Avalanche CLI..."

# Ensure Python 3 is available; exit if not
if command -v python3 > /dev/null 2>&1; then
    PYTHON_CMD=python3
elif command -v python > /dev/null 2>&1 && python --version 2>&1 | grep -q "Python 3"; then
    PYTHON_CMD=python
else
    echo "Python 3 could not be found. Please install Python 3."
    exit 1
fi

# Select pip3 or pip; exit if missing
if command -v pip3 > /dev/null 2>&1; then
    PIP_CMD=pip3
elif command -v pip > /dev/null 2>&1; then
    PIP_CMD=pip
else
    echo "Pip could not be found. Please install pip."
    exit 1
fi

echo "Using $PYTHON_CMD and $PIP_CMD"

# Install 'av' in editable mode
echo "Installing 'av' in editable mode for direct code updates..."
if $PIP_CMD install --editable . ; then    
    echo "Avalanche CLI installed, as follows:"
    $PIP_CMD show -f av
    echo "Use 'av --help' for further usage."
else
    echo "Installation of Avalanche CLI failed"
    exit 1
fi