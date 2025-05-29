# AI Voice Sales Agent

This project implements an AI-powered Voice Sales Agent capable of making simulated automated phone calls to potential customers to pitch online courses. It features natural conversation capabilities, objection handling, and a FastAPI backend, primarily utilizing CPU for AI model inference.

**Live Demo Video:** [Link to your 3-5 minute demo video - if applicable for submission]

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

### 3.Set Up Python Virtual Environment
    It's highly recommended to use a virtual environment to manage project dependencies.

    # Create a virtual environment (e.g., named 'venv')
    python -m venv venv

    # Activate the virtual environment
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate


4. Install Dependencies
Create a requirements.txt file in your project root with the following content:
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


Then, install the packages:
pip install -r requirements.txt


5. Configure Environment Variables
Create a .env.example file in the project root directory (AI_VOICE_CLIENT-MAIN/) with the following content:
# .env.example
APP_TITLE="AI Voice Sales Agent"
LOG_LEVEL="INFO"

# LLM Configuration (Hugging Face Transformers based)
LLM_MODEL_REPO_ID="Qwen/Qwen2-0.5B-Instruct"

# STT Configuration
WHISPER_MODEL_SIZE="base" # Options: tiny, base, small, medium, large (or .en versions)

# Course Details (used in prompts)
# LLM Configuration (Hugging Face - Qwen)
HUGGINGFACEHUB_API_TOKEN="your_huggingface_api_token_here" # Get from hf.co/settings/tokens
LLM_MODEL_REPO_ID="Qwen/Qwen2-0.5B-Instruct"

# App Configuration
APP_TITLE="AI Voice Sales Agent (Qwen LLM)"
APP_VERSION="0.3.0"
LOG_LEVEL="INFO"
HF_HOME = 
# STT Configuration (Whisper model size)
# Options: "tiny", "base", "small", "medium", "large"
WHISPER_MODEL_SIZE="base"

# Course Information
COURSE_NAME="AI Mastery Bootcamp"
COURSE_DURATION="12 weeks"
COURSE_PRICE_FULL="$499"
COURSE_PRICE_SPECIAL="$299"
COURSE_BENEFITS_LIST='["Learn LLMs, Computer Vision, and MLOps", "Hands-on projects", "Job placement assistance", "Certificate upon completion"]'


2.Create a .env file by copying .env.example:
cp .env.example .env

3.Open the .env file and adjust any values if necessary (though the defaults should work for a basic run).

6.Model Downloads (Automatic on First Run)
The first time you run the application or a test script that initializes the LLM or STT services, the necessary models (Qwen/Qwen2-0.5B-Instruct from Hugging Face and the Whisper model) will be downloaded and cached locally. This may take some time and requires an internet connection.
The cache location is configured to be .huggingface_cache_project/ within the project root.
Running the Application
1. Start the FastAPI Server
The server hosts the API endpoints and WebSocket for communication.
# Ensure your virtual environment is activated
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload



--reload is for development; it automatically restarts the server on code changes.
The server will be accessible at http://localhost:8000.
API documentation (Swagger UI) will be at http://localhost:8000/docs.
Health check endpoint: http://localhost:8000/health.
Observe Server Logs: Upon startup, check the console for logs indicating successful initialization of LLM, STT, and TTS services. It should confirm the LLM is running on CPU.
2. Run a Client Application
You have two command-line clients for interacting with the agent:
A. Interactive Voice Chat (Local, Direct Service Test)
This script tests the core STT, LLM, and TTS services locally without going through the FastAPI server. Good for quick checks of the AI components.
# Open a new terminal, activate venv
python interactive_voice_chat.py


Follow the prompts to enter your name and interact with your voice.
B. WebSocket Voice Client (Full End-to-End Test)
This client connects to the running FastAPI server via WebSockets for a full voice chat experience.
# Ensure the FastAPI server is running in another terminal
# Open a new terminal, activate venv
python websocket_voice_client.py


Follow the prompts to enter your name. Press Enter to start speaking, and Enter again to stop.
Running Tests
The project includes several test scripts to verify individual components. Run these from the project root with your virtual environment activated:
python test_scripts/test_config.py: Checks configuration loading.
python test_scripts/test_stt_service.py: Tests Speech-to-Text (includes live recording).
python test_scripts/test_tts_service.py: Tests Text-to-Speech.
python test_scripts/test_llm_service.py: Tests the LLM service (using local transformers on CPU).
python test_scripts/test_conversation_manager_with_real_llm.py: Tests the conversation manager with the actual LLM and LCEL chain.

Performance Notes
CPU Bound: This project is configured to run AI models (LLM, STT) on the CPU using the Hugging Face transformers library. As a result, there will be noticeable latency (e.g., 4-5 seconds or more per LLM response) during conversation turns.
Optimization: For significantly lower latency, GPU acceleration or specialized CPU runtimes (like Llama.cpp) would be required. This setup prioritizes broader compatibility and easier initial setup by focusing on CPU execution with standard libraries.


Troubleshooting
ffmpeg not found: Ensure ffmpeg is installed and in your system's PATH. This is crucial for Whisper.
Model download issues: Check your internet connection. If downloads are interrupted, delete the partial contents from .huggingface_cache_project/ and try again.
Microphone/Speaker issues: Ensure your OS has the correct audio input/output devices selected and that the Python scripts have permission to access them.
Import Errors: Double-check that all packages in requirements.txt are installed in your active virtual environment.
Slow Performance: This is expected with LLMs on CPU. See "Performance Notes."
Future Enhancements (Potential)
GPU acceleration for LLM and STT.
Integration of faster local TTS engines (e.g., Piper TTS, Coqui TTS).
Implementation of Retrieval Augmented Generation (RAG) for a more extensive knowledge base.
Full end-to-end audio streaming for improved perceived real-time interaction.
A simple web interface for testing.