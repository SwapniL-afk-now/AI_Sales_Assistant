# Project Architecture - AI Sales Assistant

This document outlines the architecture of the AI Sales Assistant project, detailing its components, directory structure, and data flow.

## 1. Overview

The AI Sales Assistant is a Python-based application designed to simulate voice-based sales conversations. It uses a Large Language Model (LLM) for generating responses, Speech-to-Text (STT) for transcribing user audio, and Text-to-Speech (TTS) for vocalizing AI responses. The backend is built with FastAPI, offering both HTTP and WebSocket endpoints for interaction. A Python WebSocket client is provided for demonstrating real-time voice chat.

## 2. Core Components

*   **FastAPI Backend (`app`):**
    *   Serves as the main application server.
    *   Handles HTTP requests for call management and text-based interactions.
    *   Provides a WebSocket endpoint for real-time voice communication.
    *   Orchestrates the interaction between different services (LLM, STT, TTS).
*   **Language Model Service (`app.services.llm_service.LocalQwenLLM`):**
    *   Integrates with a locally run Qwen language model (e.g., `Qwen/Qwen2-0.5B-Instruct`) via the Hugging Face `transformers` library.
    *   Wrapped in a custom LangChain `LLM` class for potential future LCEL chain integration.
    *   Responsible for generating intelligent and contextually relevant responses based on sales prompts and conversation history.
*   **Speech-to-Text Service (`app.services.stt_service.STTService`):**
    *   Uses OpenAI's Whisper model (e.g., `base` model) to transcribe audio input from the user into text.
*   **Text-to-Speech Service (`app.services.tts_service.TTSService`):**
    *   Uses `pyttsx3` to synthesize text responses from the AI agent into audible speech (WAV format).
*   **Conversation Manager (`app.core.conversation_manager.ConversationManager`):**
    *   Manages active call sessions.
    *   Maintains conversation history for each call.
    *   Interfaces with the LLM service (via an LCEL-like chain) to process customer input and generate agent replies.
    *   Determines conversation flow and when a call should end.
*   **WebSocket Voice Client (`websocket_voice_client.py`):**
    *   A Python client application that connects to the FastAPI WebSocket endpoint.
    *   Captures microphone audio from the user.
    *   Streams audio to the server.
    *   Receives audio from the server and plays it back to the user.
    *   Displays transcripts and system messages.

## 3. Directory Structure

    ```text
    AI_SALES_ASSISTANT/
    ├── app/                      # Main application module
    │   ├── api/                  # API endpoint definitions
    │   │   └── v1/
    │   │       ├── __init__.py
    │   │       └── endpoints/
    │   │           ├── __init__.py
    │   │           └── call_router.py  # Router for call-related endpoints
    │   ├── core/                 # Core logic, configuration, conversation management
    │   │   ├── __init__.py
    │   │   ├── config.py         # Application settings, environment variables
    │   │   └── conversation_manager.py # Manages call sessions and LLM interaction
    │   ├── models/               # Pydantic models for API requests/responses (data shapes)
    │   │   ├── __init__.py
    │   │   └── call_models.py
    │   ├── prompts/              # LLM prompt templates and formatting
    │   │   ├── __init__.py
    │   │   └── sales_prompts.py
    │   ├── schemas/              # Pydantic models for internal data structures (e.g., conversation state)
    │   │   ├── __init__.py
    │   │   └── conversation.py
    │   ├── services/             # External service integrations (LLM, STT, TTS)
    │   │   ├── __init__.py
    │   │   ├── llm_service.py
    │   │   ├── stt_service.py
    │   │   └── tts_service.py
    │   ├── __init__.py
    │   └── main.py               # FastAPI application entry point
    ├── docs/                     # Project documentation (like this file)
    │   ├── api_documentation.md
    │   ├── architecture.md
    │   └── model_selection_justification.md
    ├── test_scripts/             # (Optional) Test scripts
    ├── .env.example              # Example environment variables
    ├── .gitattributes
    ├── .gitignore
    ├── interactive_voice_chat.py # (Likely an older or alternative client script)
    ├── README.md
    ├── requirements.txt          # Python dependencies
    └── websocket_voice_client.py # Interactive WebSocket client for voice chat


*   `app/api/`: Contains API routing logic, separating different versions or concerns. `call_router.py` defines all sales call related endpoints.
*   `app/core/`: Houses central application logic. `config.py` manages settings, and `conversation_manager.py` is key for handling call state and LLM interactions.
*   `app/models/`: Pydantic models defining the structure of data exchanged via the API (request/response bodies).
*   `app/prompts/`: Stores and formats the prompts used to guide the LLM's behavior.
*   `app/schemas/`: Pydantic models for internal data representation, like `CallSession` and `Utterance`.
*   `app/services/`: Modules for interacting with external services or complex functionalities like LLM, STT, and TTS.
*   `app/main.py`: Initializes the FastAPI application, includes routers, and manages application lifespan events (startup/shutdown).
*   `websocket_voice_client.py`: A standalone script to interact with the voice chat WebSocket endpoint.

## 4. High-Level Data Flow (WebSocket Voice Chat)

1.  **Initiate Call (HTTP):**
    *   Client sends a `POST` request to `/api/v1/sales/start-call` with customer details.
    *   Server's `ConversationManager` creates a new `CallSession`, generates an initial greeting via `LLMService`.
    *   Server responds with `call_id` and the first agent message (text).

2.  **Establish WebSocket Connection:**
    *   Client uses the `call_id` to connect to `ws://localhost:8000/api/v1/sales/ws/voice-chat/{call_id}`.
    *   Server accepts the connection.
    *   Server's `call_router` retrieves the initial `CallSession`.
    *   Server uses `TTSService` to synthesize the first agent message from history (if any) and sends the audio bytes to the client.

3.  **User Speaks & Client Sends Audio:**
    *   Client records audio from the user's microphone.
    *   Client sends the raw audio data (e.g., WAV bytes) over the WebSocket to the server.

4.  **Server Processes Audio & Generates Response:**
    *   Server receives audio bytes.
    *   `STTService` (Whisper) transcribes the audio to text.
    *   Server sends the `user_text` transcript back to the client (for display).
    *   The transcribed text is passed to `ConversationManager`.
    *   `ConversationManager` updates the call history and uses its `sales_chain` (which invokes the `LLMService` with the current context and user input) to generate the agent's textual reply.
    *   `TTSService` (pyttsx3) synthesizes the agent's text reply into audio (WAV bytes).

5.  **Server Sends Audio Response:**
    *   Server sends the synthesized agent audio bytes back to the client over WebSocket.
    *   If TTS fails, a JSON message `{"type": "agent_text", "text": "..."}` is sent as a fallback.

6.  **Client Plays Audio:**
    *   Client receives the agent's audio bytes.
    *   Client plays the audio through the user's speakers.

7.  **Loop & Call Termination:**
    *   Steps 3-6 repeat for subsequent turns in the conversation.
    *   The call can end if:
        *   The LLM includes `[END_CALL]` in its response.
        *   An unrecoverable error occurs.
        *   The client explicitly requests to end the connection (if such a mechanism is fully implemented).
    *   When the call ends, the server sends a system message (e.g., `{"type": "system", "message": "Call ended."}`) and closes the WebSocket connection.

## 5. Key Technologies Used

*   **Python:** Primary programming language.
*   **FastAPI:** High-performance web framework for building APIs.
*   **Pydantic:** Data validation and settings management.
*   **Uvicorn:** ASGI server for FastAPI.
*   **WebSockets:** For real-time bidirectional communication.
*   **Hugging Face Transformers:** For loading and running the local Qwen LLM.
*   **PyTorch:** Backend for Hugging Face Transformers.
*   **OpenAI Whisper:** For Speech-to-Text.
*   **pyttsx3:** For Text-to-Speech.
*   **LangChain Core:** For structuring LLM interactions (custom LLM wrapper and prompt templates).
*   **Sounddevice & SoundFile:** Used by the client for audio recording and playback.
*   **Loguru:** For flexible and powerful logging.

---