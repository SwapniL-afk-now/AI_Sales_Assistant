# AI Voice Sales Agent

A Python-based AI Voice Sales Agent using FastAPI, LangChain, and local LLMs (Qwen2-0.5B-Instruct) for simulated sales calls.

## Prerequisites

*   Python 3.10+
*   Pip & Git
*   Microphone & Speakers
*   `ffmpeg`:
    *   Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html), add `bin` to PATH.
    *   Linux: `sudo apt-get install ffmpeg`
    *   macOS: `brew install ffmpeg`

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/SwapniL-afk-now/AI_Sales_Assistant.git # Replace with your repo URL
    cd AI_VOICE_CLIENT-MAIN
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    Ensure you have a `requirements.txt` file in the project root (see detailed README for full content if needed).
    ```bash
    pip install -r requirements.txt
    ```
    *(Key dependencies include: `fastapi`, `uvicorn`, `torch`, `transformers`, `accelerate`, `langchain-core`, `openai-whisper`, `pyttsx3`, `sounddevice`, `soundfile`, `numpy`, `websockets`, `python-dotenv`)*

4.  **Configure Environment Variables:**
    *   Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit `.env` if necessary. Key variables:
        *   `LLM_MODEL_REPO_ID="Qwen/Qwen2-0.5B-Instruct"`
        *   `HF_HOME="./.huggingface_cache_project"` (for model caching)
        *   `WHISPER_MODEL_SIZE="base"`
        *   Course details (e.g., `COURSE_NAME`)

5.  **Model Downloads (Automatic on First Run):**
    Models (LLM & Whisper) will download automatically when the app or services are first run. This requires an internet connection and may take time. They will be cached in the `HF_HOME` directory.

## Running the Application

1.  **Start the FastAPI Server on one terminal:**
    ```bash
    # Ensure virtual environment is activated
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    *   Server: `http://localhost:8000`
    *   API Docs: `http://localhost:8000/docs`

2.  **Run a Client (Example: WebSocket Client) on a second terminal:**
    ```bash
    # In a new terminal, activate venv
    python websocket_voice_client.py
    ```
    Follow prompts to interact.

## License

MIT License (or specify your chosen license)