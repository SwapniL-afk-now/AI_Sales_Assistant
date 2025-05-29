Okay, I've taken your content and structured it into a comprehensive README.md file that adheres to common GitHub best practices. This includes:

Clear Title and Badges: A main title and placeholder badges for Python version and License.

Table of Contents: Automatically generated for easy navigation, especially important for longer READMEs.

Distinct Sections: Using appropriate heading levels (H2, H3) for clear separation of topics.

Formatted Code Blocks: Using fenced code blocks with language identifiers (e.g., bash, python, text, dotenv) for commands, file contents, and the project structure.

Bulleted and Numbered Lists: For readability of features, prerequisites, steps, etc.

Emphasis: Using backticks for inline code/filenames (like_this) and bolding for emphasis.

Clarity in Instructions: Making sure steps are distinct and easy to follow.

Consolidated .env.example: I've cleaned up the .env.example section to remove redundancies and provide a clear, usable template.

Standard Sections: Added "Contributing" and "License" sections, which are standard for open-source projects.

Here's the complete README.md:

# AI Voice Sales Agent

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Choose your license -->

This project implements an AI-powered Voice Sales Agent capable of making simulated automated phone calls to potential customers to pitch online courses. It features natural conversation capabilities, objection handling, and a FastAPI backend, primarily utilizing CPU for AI model inference.

**Live Demo Video:** [Link to your 3-5 minute demo video - if applicable for submission]

## Table of Contents

- [Core Features](#core-features)
- [Project Structure](#project-structure)
- [Technical Stack](#technical-stack)
- [Setup Instructions](#setup-instructions)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Clone the Repository](#2-clone-the-repository)
  - [3. Set Up Python Virtual Environment](#3-set-up-python-virtual-environment)
  - [4. Install Dependencies](#4-install-dependencies)
  - [5. Configure Environment Variables](#5-configure-environment-variables)
  - [6. Model Downloads (Automatic on First Run)](#6-model-downloads-automatic-on-first-run)
- [Running the Application](#running-the-application)
  - [1. Start the FastAPI Server](#1-start-the-fastapi-server)
  - [2. Run a Client Application](#2-run-a-client-application)
- [Running Tests](#running-tests)
- [Performance Notes](#performance-notes)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

## Core Features

*   **Voice Conversation System:**
    *   Text-to-Speech (TTS) capability using `pyttsx3`.
    *   Speech-to-Text (STT) capability using OpenAI Whisper (via the `whisper` library).
    *   Real-time conversation flow management via WebSockets.
*   **Sales Intelligence:**
    *   Dynamic conversation scripts driven by a local Qwen2-0.5B-Instruct LLM (via Hugging Face `transformers` library on CPU).
    *   Objection handling and lead qualification logic embedded within the LLM's prompting.
*   **Backend API:**
    *   FastAPI server providing HTTP and WebSocket endpoints.
    *   Conversation state management.
*   **LangChain Integration:**
    *   Uses `langchain-core` for message structuring (`HumanMessage`, `AIMessage`).
    *   Employs `ChatPromptTemplate` and LangChain Expression Language (LCEL) for managing conversation flow with the LLM.
    *   Custom LangChain `LLM` wrapper for the local Qwen model loaded via `transformers`.

## Project Structure


AI_VOICE_CLIENT-MAIN/
├── app/
│ ├── api/
│ │ └── v1/
│ │ └── endpoints/
│ │ └── call_router.py
│ ├── core/
│ │ ├── config.py
│ │ ├── conversation_manager.py
│ │ └── rag_setup.py (Present if RAG was added, can be omitted if not)
│ ├── models/ (Pydantic models for API)
│ │ └── call_models.py
│ ├── prompts/
│ │ └── sales_prompts.py
│ ├── schemas/ (Pydantic schemas for data structures)
│ │ └── conversation.py
│ └── services/
│ ├── init.py # As listed in your structure
│ ├── llm_service.py # Uses Hugging Face Transformers
│ ├── stt_service.py
│ └── tts_service.py
├── .huggingface_cache_project/ (Local cache for Hugging Face models)
│ └── ... # Contents of cache, gitignored
├── test_scripts/ # Folder for test scripts
│ ├── init.py # As listed in your structure
│ ├── test_config.py
│ ├── test_llm_service.py
│ ├── test_stt_service.py
│ ├── test_tts_service.py
│ ├── test_conversation_manager_with_real_llm.py
│ └── test_http_endpoints.py
├── venv/ (Python virtual environment)
│ └── ... # Contents of virtual environment, gitignored
├── .env
├── .env.example
├── .gitignore
├── interactive_voice_chat.py (CLI for local voice interaction)
├── websocket_voice_client.py (CLI for WebSocket based voice interaction)
├── main.py (FastAPI application entry point)
├── requirements.txt
└── README.md

## Technical Stack

*   **Language:** Python 3.10+
*   **Backend Framework:** FastAPI
*   **AI Framework:** LangChain
*   **LLM:** Qwen2-0.5B-Instruct (via Hugging Face `transformers` library, running on CPU)
*   **STT:** OpenAI Whisper (via `whisper` library)
*   **TTS:** `pyttsx3` (utilizing OS-level speech engines)
*   **WebSocket Communication:** `websockets` library (used by FastAPI)
*   **Audio Handling:** `sounddevice`, `soundfile`, `numpy`
*   **Model Loading & Management:** Hugging Face `transformers`, `accelerate` (for `device_map="cpu"`)

## Setup Instructions

### 1. Prerequisites

*   **Python:** Version 3.10 or newer.
*   **Pip:** Python package installer.
*   **Git:** For cloning the repository.
*   **Microphone and Speakers/Headphones:** For voice interaction.
*   **`ffmpeg`:** Required by the `whisper` library for audio processing.
    *   **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, and add the `bin` directory to your system's PATH.
    *   **Linux:** `sudo apt-get install ffmpeg` (or `yum install ffmpeg`).
    *   **macOS:** `brew install ffmpeg`.

### 2. Clone the Repository

```bash
git clone [URL_OF_YOUR_REPOSITORY] # Replace [URL_OF_YOUR_REPOSITORY] with your actual repo URL
cd AI_VOICE_CLIENT-MAIN
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
3. Set Up Python Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

# Create a virtual environment (e.g., named 'venv')
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END
4. Install Dependencies

Create a requirements.txt file in your project root with the following content (if it doesn't exist already or needs updating):

# requirements.txt
fastapi
uvicorn[standard]
python-dotenv
pydantic-settings
loguru
torch
transformers
accelerate
# For LangChain core and custom LLM wrapper
langchain-core
# For STT (OpenAI Whisper)
openai-whisper
# For TTS
pyttsx3
# For audio I/O and processing
sounddevice
soundfile
numpy
# For WebSocket client (if testing separately) and FastAPI WebSockets
websockets
# For HTTP client in tests
requests
# Optional, but good for LangChain integrations (if you expand later)
# langchain-community
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Text
IGNORE_WHEN_COPYING_END

Then, install the packages:

pip install -r requirements.txt
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END
5. Configure Environment Variables

Create .env.example (Template for Environment Variables):
Ensure a file named .env.example exists in the project root directory (AI_VOICE_CLIENT-MAIN/). This file serves as a template for your actual configuration. If it's missing or needs updating, use the following content:

# .env.example

# App Configuration
APP_TITLE="AI Voice Sales Agent (Qwen LLM)"
APP_VERSION="0.3.0"
LOG_LEVEL="INFO" # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# LLM Configuration (Hugging Face Transformers based)
# For Qwen models, a token is not strictly required for download if public,
# but good practice for accessing gated models or increasing rate limits.
# Get from https://huggingface.co/settings/tokens
HUGGINGFACE_API_TOKEN="your_huggingface_api_token_here_if_needed"
LLM_MODEL_REPO_ID="Qwen/Qwen2-0.5B-Instruct"
# This directs Hugging Face libraries to use a local cache directory.
# The path should be relative to the project root or an absolute path.
HF_HOME="./.huggingface_cache_project"

# STT Configuration (OpenAI Whisper model size)
# Options: "tiny", "base", "small", "medium", "large", "tiny.en", "base.en", etc.
WHISPER_MODEL_SIZE="base"

# Course Information (used in prompts for the sales agent)
COURSE_NAME="AI Mastery Bootcamp"
COURSE_DURATION="12 weeks"
COURSE_PRICE_FULL="$499"
COURSE_PRICE_SPECIAL="$299"
COURSE_BENEFITS_LIST='["Learn LLMs, Computer Vision, and MLOps", "Hands-on projects", "Job placement assistance", "Certificate upon completion"]'
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Dotenv
IGNORE_WHEN_COPYING_END

Create your .env file:
Copy the .env.example to create your actual environment file:

cp .env.example .env
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Adjust .env values:
Open the newly created .env file and adjust any values if necessary. The defaults provided in .env.example should work for a basic run, but you might want to add your HUGGINGFACE_API_TOKEN or change model preferences.
Important: The .env file contains sensitive information or local configurations and should not be committed to version control. Ensure it's listed in your .gitignore file.

6. Model Downloads (Automatic on First Run)

The first time you run the application or a test script that initializes the LLM or STT services, the necessary models (e.g., Qwen/Qwen2-0.5B-Instruct from Hugging Face and the Whisper model) will be downloaded.

These models will be cached locally in the directory specified by the HF_HOME environment variable (default is .huggingface_cache_project/ in the project root, as per the .env.example).

This process may take some time and requires an active internet connection.

Running the Application
1. Start the FastAPI Server

The server hosts the API endpoints and WebSocket for communication.

# Ensure your virtual environment is activated
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

--reload is for development; it automatically restarts the server on code changes. Remove this flag for production.

The server will be accessible at http://localhost:8000.

API documentation (Swagger UI) will be available at http://localhost:8000/docs.

A health check endpoint is available at http://localhost:8000/health.

Observe Server Logs: Upon startup, check the console for logs indicating successful initialization of LLM, STT, and TTS services. It should confirm the LLM is running on CPU (unless configured otherwise).

2. Run a Client Application

You have two command-line clients for interacting with the agent:

A. Interactive Voice Chat (Local, Direct Service Test)

This script tests the core STT, LLM, and TTS services locally, bypassing the FastAPI server. It's useful for quick checks of the individual AI components.

# Open a new terminal, ensure your virtual environment is activated
python interactive_voice_chat.py
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Follow the prompts to enter your name and interact using your voice.

B. WebSocket Voice Client (Full End-to-End Test)

This client connects to the running FastAPI server via WebSockets for a complete voice chat experience, testing the entire system.

# Ensure the FastAPI server is running in another terminal
# Open a new terminal, ensure your virtual environment is activated
python websocket_voice_client.py
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Follow the prompts to enter your name. Press Enter to start speaking, and Enter again to stop and send your audio.

Running Tests

The project includes several test scripts in the test_scripts/ directory to verify individual components. Run these from the project root with your virtual environment activated.

To check configuration loading:

python test_scripts/test_config.py
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

To test Speech-to-Text (may include live recording):

python test_scripts/test_stt_service.py
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

To test Text-to-Speech:

python test_scripts/test_tts_service.py
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

To test the LLM service (using local transformers on CPU):

python test_scripts/test_llm_service.py
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

To test the conversation manager with the actual LLM and LCEL chain:

python test_scripts/test_conversation_manager_with_real_llm.py
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

To test HTTP endpoints (ensure the FastAPI server is running first):

# Terminal 1: Start server (if not already running)
# uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Run HTTP tests
python test_scripts/test_http_endpoints.py
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END
Performance Notes

CPU Bound: This project is configured to run AI models (LLM, STT) on the CPU using the Hugging Face transformers library. As a result, there will be noticeable latency (e.g., 4-5 seconds or more per LLM response) during conversation turns.

Optimization: For significantly lower latency, GPU acceleration or specialized CPU runtimes (like Llama.cpp for some models) would be required. This setup prioritizes broader compatibility and easier initial setup by focusing on CPU execution with standard libraries.

Troubleshooting

ffmpeg not found: Ensure ffmpeg is installed and accessible in your system's PATH. This is crucial for the whisper library.

Model download issues: Check your internet connection. If downloads are interrupted, you might need to clear the partial contents from your HF_HOME directory (e.g., .huggingface_cache_project/) and try again.

Microphone/Speaker issues: Ensure your operating system has the correct audio input/output devices selected and that the Python scripts have the necessary permissions to access them.

Import Errors: Double-check that all packages listed in requirements.txt are correctly installed in your active virtual environment (you can verify with pip list).

Slow Performance: This is expected with the current configuration running LLMs on CPU. Refer to "Performance Notes."

Future Enhancements

GPU acceleration for LLM and STT to significantly reduce latency.

Integration of faster local TTS engines (e.g., Piper TTS, Coqui TTS).

Implementation of Retrieval Augmented Generation (RAG) for a more extensive and dynamic knowledge base.

Full end-to-end audio streaming for improved perceived real-time interaction (reduces start-stop feeling).

A simple web interface (e.g., using Streamlit or Gradio) for easier testing and demonstration.

Contributing

Contributions are welcome! If you'd like to contribute, please follow these steps:

Fork the repository.

Create a new branch (git checkout -b feature/your-feature-name).

Make your changes and commit them (git commit -m 'Add some feature').

Push to the branch (git push origin feature/your-feature-name).

Open a Pull Request.

Please make sure to update tests as appropriate.

License

This project is licensed under the MIT License - see the LICENSE.md file for details.
(Note: You'll need to create a LICENSE.md file in your repository. If you choose MIT, you can find a template easily online.)

IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END