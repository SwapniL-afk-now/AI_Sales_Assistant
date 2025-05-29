# API Documentation - AI Sales Assistant

This document provides details about the API endpoints for the AI Sales Assistant project.

## Base URL

All API endpoints are prefixed with: `/api/v1/sales`

## HTTP Endpoints

These endpoints are used for initiating calls, sending text-based responses, and retrieving conversation history.

---

### 1. Start a New Call

*   **Endpoint:** `POST /start-call`
*   **Description:** Initiates a new sales call session with a customer. The AI agent will generate an initial greeting.
*   **Request Body:** `application/json`
    ```json
    {
      "phone_number": "123-456-7890",
      "customer_name": "John Doe"
    }
    ```
    *   `phone_number` (string, required): The phone number of the customer.
    *   `customer_name` (string, required): The name of the customer.
*   **Success Response (201 Created):** `application/json`
    ```json
    {
      "call_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "first_message": "Hi John Doe, this is Alex from Edvantage AI. I'm calling to chat briefly about our new AI Mastery Bootcamp. Is now an okay time to talk for a couple of minutes?"
    }
    ```
    *   `call_id` (string): A unique identifier for the call session.
    *   `first_message` (string): The initial greeting from the AI sales agent.
*   **Error Responses:**
    *   `400 Bad Request`: If the request body is malformed or missing required fields.
    *   `503 Service Unavailable`: If the LLM service is not ready or unavailable.

---

### 2. Respond to Call (Text)

*   **Endpoint:** `POST /respond/{call_id}`
*   **Description:** Sends a customer's text message to an active call session and gets the AI agent's reply.
*   **Path Parameters:**
    *   `call_id` (string, required): The ID of the active call session.
*   **Request Body:** `application/json`
    ```json
    {
      "message": "I'm interested, tell me more."
    }
    ```
    *   `message` (string, required): The customer's text message.
*   **Success Response (200 OK):** `application/json`
    ```json
    {
      "reply": "Great! Our AI Mastery Bootcamp is a 12-week program covering LLMs, Computer Vision, and MLOps. We currently have a special offer price of $299.",
      "should_end_call": false
    }
    ```
    *   `reply` (string): The AI sales agent's response.
    *   `should_end_call` (boolean): Indicates if the agent determined the call should end.
*   **Error Responses:**
    *   `400 Bad Request`: If the message is empty.
    *   `404 Not Found`: If the `call_id` is not found or the call has ended.
    *   `503 Service Unavailable`: If the LLM service is not ready or unavailable.

---

### 3. Respond to Call (Audio)

*   **Endpoint:** `POST /respond-audio/{call_id}`
*   **Description:** Sends customer's spoken audio to an active call session. The audio is transcribed, then processed by the LLM to get the AI agent's reply.
*   **Path Parameters:**
    *   `call_id` (string, required): The ID of the active call session.
*   **Request Body:** `multipart/form-data`
    *   `audio_file` (file, required): The audio file (e.g., WAV, MP3) containing the customer's speech.
*   **Success Response (200 OK):** `application/json`
    ```json
    {
      "reply": "Certainly! The hands-on projects are designed to give you practical experience. For example, you'll build a recommendation system and deploy a computer vision model.",
      "should_end_call": false
    }
    ```
    *   `reply` (string): The AI sales agent's text response (to be synthesized to audio by the client or a TTS step if added here).
    *   `should_end_call` (boolean): Indicates if the agent determined the call should end.
*   **Error Responses:**
    *   `400 Bad Request`: If the audio file is empty or unreadable.
    *   `404 Not Found`: If the `call_id` is not found or the call has ended.
    *   `500 Internal Server Error`: If STT fails.
    *   `503 Service Unavailable`: If STT or LLM service is unavailable.

---

### 4. Get Conversation History

*   **Endpoint:** `GET /conversation/{call_id}`
*   **Description:** Retrieves the full conversation history for a given call session.
*   **Path Parameters:**
    *   `call_id` (string, required): The ID of the call session.
*   **Success Response (200 OK):** `application/json`
    ```json
    {
      "call_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "customer_name": "John Doe",
      "phone_number": "123-456-7890",
      "history": [
        {
          "speaker": "agent",
          "text": "Hi John Doe, this is Alex from Edvantage AI...",
          "timestamp": "2023-10-27T10:00:00Z"
        },
        {
          "speaker": "customer",
          "text": "I'm interested, tell me more.",
          "timestamp": "2023-10-27T10:00:30Z"
        },
        {
          "speaker": "agent",
          "text": "Great! Our AI Mastery Bootcamp is a 12-week program...",
          "timestamp": "2023-10-27T10:01:00Z"
        }
      ],
      "is_active": true,
      "start_time": "2023-10-27T10:00:00Z",
      "end_time": null
    }
    ```
*   **Error Responses:**
    *   `404 Not Found`: If the `call_id` is not found.

---

## WebSocket Endpoint

This endpoint facilitates real-time, full-duplex voice communication between the client and the AI sales agent.

### 1. Voice Chat

*   **Endpoint:** `WS /ws/voice-chat/{call_id}`
*   **Description:** Establishes a WebSocket connection for an existing call session (previously started via `POST /start-call`). Allows for streaming audio from the client to the server, and receiving synthesized audio from the server.
*   **Path Parameters:**
    *   `call_id` (string, required): The ID of the call session obtained from `POST /start-call`.

*   **Connection:**
    *   Client initiates a WebSocket connection to the specified URI.
    *   Server accepts the connection.
    *   If the `call_id` is invalid or services are unavailable, the server will send an error JSON message and close the connection.

*   **Server-to-Client Messages:**
    1.  **Initial Agent Audio (Bytes):**
        *   **Type:** `bytes`
        *   **Content:** WAV audio bytes of the agent's first message (if available from the call session history).
    2.  **Agent Audio Response (Bytes):**
        *   **Type:** `bytes`
        *   **Content:** WAV audio bytes of the agent's reply after processing client's audio.
    3.  **Agent Text Fallback (JSON):**
        *   **Type:** `string` (JSON)
        *   **Content:** If TTS fails, the server sends the agent's reply as text.
            ```json
            {"type": "agent_text", "text": "The agent's textual reply."}
            ```
    4.  **User Transcript (JSON):**
        *   **Type:** `string` (JSON)
        *   **Content:** The server sends back the transcript of the user's speech.
            ```json
            {"type": "user_text", "text": "What the user said."}
            ```
    5.  **System Messages (JSON):**
        *   **Type:** `string` (JSON)
        *   **Content:** System-level messages, e.g., indicating the call has ended.
            ```json
            {"type": "system", "message": "Call ended by agent."}
            ```
    6.  **Error Messages (JSON):**
        *   **Type:** `string` (JSON)
        *   **Content:** Errors occurring during processing (e.g., STT failure).
            ```json
            {"type": "error", "message": "STT failed: Unknown STT error"}
            ```

*   **Client-to-Server Messages:**
    1.  **Client Audio (Bytes):**
        *   **Type:** `bytes`
        *   **Content:** Raw audio bytes (expected to be WAV format, `16000 Hz`, `mono`, `PCM_16` or `float32` compatible with Whisper) of the customer's speech.
    2.  **Client Control Message (Text/JSON - Optional):**
        *   **Type:** `string`
        *   **Content:** Client might send text commands, e.g., to explicitly end the connection.
            ```text
            END_CONNECTION_REQUEST_BY_CLIENT
            ```
            or
            ```json
            {"type": "control", "command": "end_call"}
            ```
            *(Current implementation primarily expects audio bytes and handles specific text for disconnect).*

*   **Disconnection:**
    *   Either party can initiate a close.
    *   The server will close the connection if `should_end_call` becomes true, an unrecoverable error occurs, or the client sends a recognized disconnect message.

---

## Health Check

*   **Endpoint:** `GET /health`
*   **Description:** Checks the health and status of the application, particularly the LLM service.
*   **Success Response (200 OK):** `application/json`
    ```json
    {
      "status": "ok",
      "app_title": "AI Voice Sales Agent (Qwen LLM)",
      "app_version": "0.3.3",
      "llm_service_status": "ok",
      "llm_service_details": "local_llm_ready (mode: local_qwen_llm_wrapper)"
    }
    ```
    or if issues are present:
    ```json
    {
      "status": "issues_present",
      "app_title": "AI Voice Sales Agent (Qwen LLM)",
      "app_version": "0.3.3",
      "llm_service_status": "critical_issue",
      "llm_service_details": "local_llm_initialization_failed"
    }
    ```

---