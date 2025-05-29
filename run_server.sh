#!/bin/bash
# Ensure .env file exists or copy from .env.example
if [ ! -f .env ]; then
    echo "INFO: .env file not found. Attempting to copy from .env.example."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "INFO: .env file created from .env.example. Please fill in your API keys."
    else
        echo "ERROR: .env.example not found. Please create a .env file with your configuration."
        exit 1
    fi
fi

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

echo "Starting FastAPI server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-config=None