# from fastapi import APIRouter, HTTPException, Depends, status, Body, UploadFile, File
# from app.models.call_models import (
#     StartCallRequest, StartCallResponse,
#     RespondRequest, RespondResponse,
#     ConversationHistoryResponse
# )
# from app.core.conversation_manager import ConversationManager, get_conversation_manager
# from app.services.stt_service import STTService, get_stt_service
# from app.core.config import logger
# from app.schemas.conversation import CallSession
# from typing import Optional
# # from app.services.llm_service import LLMService # Import not strictly needed here as it's accessed via manager

# router = APIRouter()

# @router.post("/start-call", response_model=StartCallResponse, status_code=status.HTTP_201_CREATED)
# async def start_call(
#     request: StartCallRequest,
#     manager: ConversationManager = Depends(get_conversation_manager),
# ):
#     logger.info(f"Received /start-call request for customer: {request.customer_name}")
#     if not manager.llm_service or not manager.llm_service.is_ready(): # Check via manager
#         logger.error("LLM Service not available or not initialized. Cannot start call.")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="The AI Sales Agent is currently unavailable due to an LLM service issue. Please try again later."
#         )
    
#     call_id, first_message = manager.start_new_call(
#         customer_name=request.customer_name,
#         phone_number=request.phone_number
#     )
#     return StartCallResponse(call_id=call_id, first_message=first_message)

# @router.post("/respond/{call_id}", response_model=RespondResponse)
# async def respond_to_call(
#     call_id: str,
#     request: RespondRequest,
#     manager: ConversationManager = Depends(get_conversation_manager),
# ):
#     logger.info(f"Received /respond request for call_id: {call_id}")
#     if not manager.llm_service or not manager.llm_service.is_ready(): # Check via manager
#         logger.error("LLM Service not available or not initialized. Cannot respond to call.")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="The AI Sales Agent is currently unavailable due to an LLM service issue."
#         )

#     customer_text = request.message
#     if not customer_text:
#          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty.")

#     reply_text, should_end_call = manager.process_customer_response(call_id, customer_text)

#     if reply_text is None: 
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call ID not found or call has ended.")

#     return RespondResponse(reply=reply_text, should_end_call=should_end_call)

# @router.post("/respond-audio/{call_id}", response_model=RespondResponse)
# async def respond_to_call_audio(
#     call_id: str,
#     audio_file: UploadFile = File(...),
#     manager: ConversationManager = Depends(get_conversation_manager),
#     stt: STTService = Depends(get_stt_service)
# ):
#     logger.info(f"Received /respond-audio request for call_id: {call_id}, audio_file: {audio_file.filename}")

#     if not stt or not stt.model:
#         logger.error("STT Service not available or model not loaded. Cannot process audio.")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Speech-to-Text service is currently unavailable. Please try again later."
#         )

#     if not manager.llm_service or not manager.llm_service.is_ready(): # Check via manager
#         logger.error("LLM Service not available or not initialized. Cannot respond to audio call.")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="The AI Sales Agent is currently unavailable due to an LLM service issue."
#         )

#     try:
#         audio_bytes = await audio_file.read()
#         if not audio_bytes:
#             logger.warning("Received empty audio file.")
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file is empty.")
#         logger.info(f"Audio file read successfully, size: {len(audio_bytes)} bytes")
#     except Exception as e:
#         logger.error(f"Error reading audio file: {e}", exc_info=True)
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read audio file: {e}")
#     finally:
#         await audio_file.close()

#     customer_text = stt.transcribe_audio(audio_bytes)
#     logger.info(f"STT transcription result: '{customer_text}'")

#     if customer_text is None or \
#        "Error: STT service not available." in customer_text or \
#        "Error during transcription:" in customer_text:
#         logger.error(f"STT failed or returned an error string: {customer_text}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
#             detail=f"Speech-to-Text processing failed. Details: {customer_text if customer_text else 'No transcription available'}"
#         )
    
#     stripped_customer_text = customer_text.strip()
#     if not stripped_customer_text:
#          logger.warning("Transcription resulted in empty text after stripping.")
#          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transcription resulted in empty text. Please speak clearly or check audio quality.")

#     reply_text, should_end_call = manager.process_customer_response(call_id, stripped_customer_text)

#     if reply_text is None: 
#         logger.warning(f"Conversation manager returned None for reply text. Call ID: {call_id} might not exist or be inactive.")
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call ID not found or call has ended.")

#     return RespondResponse(reply=reply_text, should_end_call=should_end_call)

# @router.get("/conversation/{call_id}", response_model=ConversationHistoryResponse)
# async def get_conversation(
#     call_id: str,
#     manager: ConversationManager = Depends(get_conversation_manager)
# ):
#     logger.info(f"Received /conversation request for call_id: {call_id}")
#     session_data: Optional[CallSession] = manager.get_conversation_history(call_id)

#     if not session_data:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found for this call ID.")

#     return ConversationHistoryResponse(
#         call_id=session_data.call_id,
#         customer_name=session_data.customer_name,
#         phone_number=session_data.phone_number,
#         history=[u.model_dump() for u in session_data.history],
#         is_active=session_data.is_active,
#         start_time=session_data.start_time.isoformat(),
#         end_time=session_data.end_time.isoformat() if session_data.end_time else None
#     )


from fastapi import (
    APIRouter, HTTPException, Depends, status, Body, UploadFile, File,
    WebSocket, WebSocketDisconnect, WebSocketException
)
from fastapi.concurrency import run_in_threadpool
from starlette.websockets import WebSocketState # For checking state if needed

from app.models.call_models import (
    StartCallRequest, StartCallResponse,
    RespondRequest, RespondResponse,
    ConversationHistoryResponse
)
from app.core.conversation_manager import ConversationManager, get_conversation_manager
from app.services.stt_service import STTService, get_stt_service
from app.services.tts_service import TTSService, get_tts_service
from app.core.config import logger
from app.schemas.conversation import CallSession
from typing import Optional
import asyncio

router = APIRouter()

# --- HTTP Endpoints (remain the same as your last correct version) ---
@router.post("/start-call", response_model=StartCallResponse, status_code=status.HTTP_201_CREATED)
async def start_call(
    request: StartCallRequest,
    manager: ConversationManager = Depends(get_conversation_manager),
):
    logger.info(f"Received /start-call request for customer: {request.customer_name}")
    if not manager.llm_service or not manager.llm_service.is_ready():
        logger.error("LLM Service not available or not initialized. Cannot start call.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI Sales Agent is currently unavailable due to an LLM service issue. Please try again later."
        )
    call_id, first_message = await run_in_threadpool(
        manager.start_new_call,
        customer_name=request.customer_name,
        phone_number=request.phone_number
    )
    return StartCallResponse(call_id=call_id, first_message=first_message)

@router.post("/respond/{call_id}", response_model=RespondResponse)
async def respond_to_call(
    call_id: str,
    request: RespondRequest,
    manager: ConversationManager = Depends(get_conversation_manager),
):
    logger.info(f"Received /respond request for call_id: {call_id}")
    if not manager.llm_service or not manager.llm_service.is_ready():
        logger.error("LLM Service not available or not initialized. Cannot respond to call.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI Sales Agent is currently unavailable due to an LLM service issue."
        )
    customer_text = request.message
    if not customer_text:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty.")
    reply_text, should_end_call = await run_in_threadpool(
        manager.process_customer_response, call_id, customer_text
    )
    if reply_text is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call ID not found or call has ended.")
    return RespondResponse(reply=reply_text, should_end_call=should_end_call)

@router.post("/respond-audio/{call_id}", response_model=RespondResponse)
async def respond_to_call_audio(
    call_id: str,
    audio_file: UploadFile = File(...),
    manager: ConversationManager = Depends(get_conversation_manager),
    stt: STTService = Depends(get_stt_service)
):
    logger.info(f"Received /respond-audio request for call_id: {call_id}, audio_file: {audio_file.filename}")
    if not stt or not stt.model: # type: ignore
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="STT service unavailable.")
    if not manager.llm_service or not manager.llm_service.is_ready():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM service unavailable.")
    try:
        audio_bytes = await audio_file.read()
        if not audio_bytes: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file empty.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read audio: {e}")
    finally: await audio_file.close()

    customer_text = await run_in_threadpool(stt.transcribe_audio, audio_bytes) # type: ignore
    if customer_text is None or "Error:" in customer_text:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"STT failed: {customer_text or 'Unknown'}")
    stripped_customer_text = customer_text.strip()
    if not stripped_customer_text:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty transcription.")
    reply_text, should_end_call = await run_in_threadpool(manager.process_customer_response, call_id, stripped_customer_text)
    if reply_text is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call ID not found or ended.")
    return RespondResponse(reply=reply_text, should_end_call=should_end_call)

@router.get("/conversation/{call_id}", response_model=ConversationHistoryResponse)
async def get_conversation(
    call_id: str,
    manager: ConversationManager = Depends(get_conversation_manager)
):
    logger.info(f"Received /conversation request for call_id: {call_id}")
    session_data = await run_in_threadpool(manager.get_conversation_history, call_id)
    if not session_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return ConversationHistoryResponse(
        call_id=session_data.call_id, customer_name=session_data.customer_name,
        phone_number=session_data.phone_number, history=[u.model_dump() for u in session_data.history],
        is_active=session_data.is_active, start_time=session_data.start_time.isoformat(),
        end_time=session_data.end_time.isoformat() if session_data.end_time else None
    )

# --- WebSocket Endpoint ---
@router.websocket("/ws/voice-chat/{call_id}")
async def websocket_voice_chat_endpoint(
    websocket: WebSocket,
    call_id: str,
):
    await websocket.accept()
    logger.info(f"WS: Connection accepted for call_id: {call_id}")

    manager = get_conversation_manager()
    stt_service = get_stt_service()
    tts_service = get_tts_service()

    if not all([manager, stt_service, tts_service, 
                stt_service.model, tts_service.engine, # type: ignore
                manager.llm_service, manager.llm_service.is_ready()]): # type: ignore
        error_msg = "A required backend service is unavailable."
        logger.error(f"WS Error for {call_id}: {error_msg}")
        await websocket.send_json({"type": "error", "message": error_msg})
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    call_session_initial = await run_in_threadpool(manager.get_conversation_history, call_id)
    if not call_session_initial:
        error_msg = f"Invalid call_id '{call_id}'. Start call via HTTP POST /start-call."
        logger.error(f"WS Error for {call_id}: {error_msg}")
        await websocket.send_json({"type": "error", "message": error_msg})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        if call_session_initial.history and call_session_initial.history[0].speaker == "agent":
            initial_agent_text = call_session_initial.history[0].text
            logger.info(f"WS: Sending initial agent message for {call_id}: {initial_agent_text}")
            agent_audio_bytes = await run_in_threadpool(tts_service.synthesize_to_wav_bytes, initial_agent_text) # type: ignore
            if agent_audio_bytes:
                await websocket.send_bytes(agent_audio_bytes)
            else:
                await websocket.send_json({"type": "agent_text", "text": initial_agent_text})

        while True:
            # Explicitly try to receive bytes first, then text as a fallback for control messages
            # This loop structure handles one message at a time.
            # For VAD, client would send audio segments, or server would buffer.
            
            # Wait for a message from the client
            message_data = await websocket.receive() # This returns a dict like {'type': 'websocket.receive', 'bytes': b'', 'text': ''}
                                                 # or {'type': 'websocket.disconnect', ...}

            if message_data["type"] == "websocket.disconnect":
                logger.info(f"WS: Client initiated disconnect for call_id: {call_id}. Code: {message_data.get('code')}")
                break # Exit the loop

            audio_bytes_from_client = None
            client_text_command = None

            if message_data.get("bytes") is not None:
                audio_bytes_from_client = message_data["bytes"]
            elif message_data.get("text") is not None:
                client_text_command = message_data["text"]
                # Potentially parse JSON if client sends structured text commands
                # For now, just log it if it's not a known command like "END_CONNECTION"
                if client_text_command.upper() == "END_CONNECTION_REQUEST_BY_CLIENT": # Example command
                    logger.info(f"WS: Client for {call_id} explicitly requested to end connection via text.")
                    await websocket.send_json({"type": "system", "message": "Connection termination acknowledged."})
                    break 
                logger.info(f"WS: Received text from client for {call_id}: {client_text_command}")
                # If text is not a command, we might ignore it or treat it as an error in a voice-only flow
                continue # For now, only process bytes for audio

            if audio_bytes_from_client is None: # Should not happen if not disconnect or text
                logger.warning(f"WS: Received message_data without bytes or text for {call_id}")
                continue

            if not audio_bytes_from_client:
                logger.info(f"WS: Received empty audio payload from client for {call_id}.")
                # Optionally, send a "didn't hear you" message back
                # For now, let STT handle empty bytes (it should produce empty text)
                # continue # Or proceed to STT

            logger.info(f"WS: Received audio (len: {len(audio_bytes_from_client)}) from {call_id}. Transcribing...")

            customer_text = await run_in_threadpool(stt_service.transcribe_audio, audio_bytes_from_client) # type: ignore
            
            if customer_text is None or "Error:" in customer_text: # Broad error check
                logger.error(f"WS: STT failed for {call_id}: {customer_text}")
                await websocket.send_json({"type": "error", "message": f"STT failed: {customer_text or 'Unknown STT error'}"})
                continue
            
            customer_text = customer_text.strip()
            # Send transcript back to client immediately for display
            await websocket.send_json({"type": "user_text", "text": customer_text})
            logger.info(f"WS: User ({call_id}) said: '{customer_text}'")

            if not customer_text: # If transcription is empty after STT and stripping
                logger.info(f"WS: Empty transcription for {call_id}.")
                empty_response_text = "I'm sorry, I didn't quite catch that. Could you please repeat?"
                empty_response_audio = await run_in_threadpool(tts_service.synthesize_to_wav_bytes, empty_response_text) # type: ignore
                if empty_response_audio: await websocket.send_bytes(empty_response_audio)
                else: await websocket.send_json({"type": "agent_text", "text": empty_response_text})
                continue

            agent_reply_text, should_end_call = await run_in_threadpool(
                manager.process_customer_response, call_id, customer_text # type: ignore
            )

            if agent_reply_text is None:
                logger.warning(f"WS: Agent reply is None for {call_id}. Ending.")
                await websocket.send_json({"type": "system", "message": "Call ended by system."})
                break

            logger.info(f"WS: Agent ({call_id}) replies: '{agent_reply_text}'")
            
            agent_audio_bytes = await run_in_threadpool(tts_service.synthesize_to_wav_bytes, agent_reply_text) # type: ignore
            if agent_audio_bytes:
                await websocket.send_bytes(agent_audio_bytes)
            else:
                logger.error(f"WS: TTS failed for {call_id}. Sending text reply.")
                await websocket.send_json({"type": "agent_text", "text": agent_reply_text})

            if should_end_call:
                logger.info(f"WS: Call for {call_id} ended by agent logic.")
                await websocket.send_json({"type": "system", "message": "Call ended by agent."})
                break

    except WebSocketDisconnect as e: # Catch specific disconnect exception
        logger.info(f"WS: WebSocket disconnected for call_id: {call_id}. Code: {e.code}, Reason: {e.reason}")
    except WebSocketException as ws_exc:
        logger.error(f"WS: WebSocketException for call_id {call_id}: {ws_exc}", exc_info=True)
    except Exception as e:
        logger.error(f"WS: Unexpected error in WebSocket for call_id {call_id}: {e}", exc_info=True)
        if websocket.client_state != WebSocketState.DISCONNECTED: # type: ignore
            try:
                await websocket.send_json({"type": "error", "message": "An unexpected server error occurred."})
            except Exception: pass # Ignore if sending error fails
    finally:
        logger.info(f"WS: Cleaning up WebSocket connection for call_id: {call_id}")
        if websocket.client_state != WebSocketState.DISCONNECTED: # type: ignore
            await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
        logger.info(f"WS: WebSocket connection fully closed for call_id: {call_id}")