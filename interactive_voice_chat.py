# interactive_voice_chat.py

import sys
import sounddevice as sd
import numpy as np
import soundfile as sf
import io
import time
import threading # For non-blocking input to stop recording

try:
    from app.core.config import logger, settings
    from app.services.stt_service import get_stt_service
    from app.services.tts_service import get_tts_service
    from app.services.llm_service import get_llm_service, LLMService
    from app.core.conversation_manager import get_conversation_manager
except ImportError as e:
    print(f"Error importing project modules: {e}")
    # ... (rest of import error handling)
    sys.exit(1)

# --- Configuration ---
# DEFAULT_RECORD_DURATION = 10  # seconds - A longer default if not using manual stop
SAMPLE_RATE = 16000  # Hz, preferred by Whisper
QUIT_COMMANDS = ["quit", "exit", "goodbye", "bye bye", "that's all"]

# --- Global for stopping recording ---
stop_recording_event = threading.Event()

def record_audio_interactive():
    """
    Records audio until Enter is pressed or a timeout is reached.
    Returns audio bytes or None.
    """
    global stop_recording_event
    stop_recording_event.clear()

    logger.info("Listening... Press ENTER to stop recording or speak for up to 20 seconds.")
    
    recorded_frames = []

    def callback(indata, frames, time, status):
        if status:
            logger.warning(f"Recording status: {status}")
        if not stop_recording_event.is_set():
            recorded_frames.append(indata.copy())
        else:
            raise sd.CallbackStop # Signal to stop the stream

    # Thread to listen for Enter key
    def listen_for_enter():
        input() # This will block until Enter is pressed
        if not stop_recording_event.is_set(): # Check if already stopped by timeout
            logger.info("Enter pressed, stopping recording.")
            stop_recording_event.set()

    input_thread = threading.Thread(target=listen_for_enter)
    input_thread.daemon = True # Allow main program to exit even if thread is running
    input_thread.start()

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32', callback=callback):
            # Wait for either the event to be set (Enter pressed) or a timeout (e.g., 20 seconds)
            # sd.sleep() is not ideal here for long durations with an event.
            # We can let the input_thread signal or use a timeout on the event wait.
            # A simple way is to let the stream run and check the event in the callback,
            # or use a timeout on event.wait() if we had a fixed max duration.

            # Let's use a timeout for the recording session itself
            timeout_seconds = 20 
            start_time = time.time()
            while not stop_recording_event.is_set() and (time.time() - start_time) < timeout_seconds :
                time.sleep(0.1) # Keep the main thread alive and check periodically

            if not stop_recording_event.is_set(): # If timeout reached before Enter
                logger.info(f"Recording timed out after {timeout_seconds} seconds.")
                stop_recording_event.set() # Ensure callback stops if it hasn't already

    except sd.CallbackStop:
        logger.debug("Recording stream stopped via CallbackStop.")
    except Exception as e:
        logger.error(f"Error during audio recording: {e}", exc_info=True)
        return None
    finally:
        # Ensure the event is set to stop any lingering stream activity if an error occurred elsewhere
        stop_recording_event.set() 
        if input_thread.is_alive():
             logger.debug("Waiting for input_thread to join (it might be stuck on input()). Give it a moment or press Enter again.")
             # input_thread.join(timeout=0.5) # Don't wait too long, user might need to press enter to release it.


    if not recorded_frames:
        logger.warning("No audio frames were recorded.")
        return None

    logger.info("Processing recorded audio.")
    recording = np.concatenate(recorded_frames, axis=0)
    
    temp_wav_bytes_io = io.BytesIO()
    sf.write(temp_wav_bytes_io, recording, SAMPLE_RATE, format='WAV', subtype='PCM_16')
    temp_wav_bytes_io.seek(0)
    return temp_wav_bytes_io.read()


def main_conversation():
    logger.info("--- Starting Interactive Voice Conversation ---")
    # ... (Service initializations remain the same as the last working version)
    logger.info("Initializing services...")
    stt_service = get_stt_service()
    tts_service = get_tts_service()
    llm_s: Optional[LLMService] = get_llm_service(force_local=True) 
    
    if not stt_service or not stt_service.model:
        logger.error("STT Service not available. Exiting.")
        return
    if not tts_service or not tts_service.engine:
        logger.error("TTS Service not available. Exiting.")
        return
    if not llm_s or not llm_s.is_ready():
        logger.error(f"LLM Service not available or not ready (Mode: {llm_s.llm_mode if llm_s else 'None'}). Exiting.")
        return
    
    manager = get_conversation_manager()
    if not manager:
        logger.error("Conversation Manager not available. Exiting.")
        return
    if not manager.llm_service or not manager.llm_service.is_ready():
        logger.error(f"LLM not properly initialized within Conversation Manager (Mode: {manager.llm_service.llm_mode if manager.llm_service else 'None'}). Exiting.")
        return
    logger.info("All services initialized.")

    customer_name = input("Enter your name to start the call: ")
    phone_number = "000-interactive"

    call_id, agent_message = manager.start_new_call(customer_name, phone_number)
    if not agent_message or "initializing" in agent_message.lower() or "unavailable" in agent_message.lower():
        logger.error(f"Failed to start call with conversation manager properly. Agent message: {agent_message}")
        if agent_message and tts_service and tts_service.engine: tts_service.speak_locally(agent_message)
        return
        
    logger.info(f"AGENT: {agent_message}")
    if tts_service and tts_service.engine: tts_service.speak_locally(agent_message)

    turn_count = 0
    max_turns = 20 # Increased max turns

    try:
        while turn_count < max_turns:
            turn_count += 1
            logger.info(f"\n--- Turn {turn_count} ---")
            # input("Press Enter to start, then Enter again to stop speaking...") # Old prompt
            
            user_audio_bytes = record_audio_interactive() # Uses the new interactive recording

            if not user_audio_bytes:
                logger.warning("No audio recorded or recording failed.")
                # Agent could say something here, or we just loop.
                # For now, let's prompt the agent to ask again if nothing was heard.
                # This requires a slight change in how we handle no user input.
                # Let's assume for now that if user_audio_bytes is None, we make the agent say "I didn't hear you"
                # This is a placeholder; a more robust flow would be better.
                if manager.llm_service and manager.llm_service.is_ready(): # type: ignore
                    agent_message, should_end_call = manager.process_customer_response(call_id, "[USER_SILENCE]") # Special token
                    if agent_message:
                        logger.info(f"AGENT (after silence): {agent_message}")
                        if tts_service and tts_service.engine: tts_service.speak_locally(agent_message)
                    if should_end_call:
                        logger.info("Call ended after user silence and agent decision.")
                        break
                else:
                    if tts_service and tts_service.engine: tts_service.speak_locally("I couldn't process that. Let's try again.")
                continue

            logger.info("Transcribing your speech...")
            user_text = stt_service.transcribe_audio(user_audio_bytes)
            
            if user_text is None or "Error" in user_text:
                logger.error(f"STT failed or returned error: {user_text}")
                if tts_service and tts_service.engine: tts_service.speak_locally("I'm having trouble understanding. Let's try that again.")
                continue
            
            user_text = user_text.strip()
            if not user_text:
                logger.info("You didn't say anything or transcription was empty.")
                # Agent could say something here.
                # Similar to above, could send a [USER_SILENCE] or similar to the LLM.
                # For simplicity for now:
                if tts_service and tts_service.engine: tts_service.speak_locally("I didn't quite catch that. Could you repeat?")
                continue

            logger.info(f"YOU ({customer_name}): {user_text}")

            # Check for quit command from user
            if user_text.lower() in QUIT_COMMANDS:
                logger.info("User requested to end the conversation.")
                agent_farewell = "Okay, goodbye for now!" # Generic farewell
                # Optionally, you could send the quit command to the LLM for a more natural farewell
                # agent_message, should_end_call = manager.process_customer_response(call_id, user_text)
                # if agent_message: agent_farewell = agent_message
                
                logger.info(f"AGENT: {agent_farewell}")
                if tts_service and tts_service.engine: tts_service.speak_locally(agent_farewell)
                break


            logger.info("Getting agent's response...")
            agent_message, should_end_call = manager.process_customer_response(call_id, user_text)

            if agent_message is None:
                logger.error("Agent response was None. Call might have ended unexpectedly.")
                if tts_service and tts_service.engine: tts_service.speak_locally("It seems our call disconnected. Goodbye.")
                break
            
            logger.info(f"AGENT: {agent_message}")
            if tts_service and tts_service.engine: tts_service.speak_locally(agent_message)

            if should_end_call:
                logger.info("Agent indicated call should end.")
                break
        
        if turn_count >= max_turns:
            logger.info("Maximum conversation turns reached.")

    except KeyboardInterrupt:
        logger.info("\nExiting conversation (Ctrl+C).")
    finally:
        logger.info("--- Conversation Ended ---")
        stop_recording_event.set() # Ensure any recording processes are signalled to stop

if __name__ == "__main__":
    main_conversation()