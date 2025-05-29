# websocket_voice_client.py
import asyncio
import websockets
import sounddevice as sd
import numpy as np
import soundfile as sf
import io
import json
import requests
import threading
import queue
import logging
import time

# ... (logging and other configurations remain the same) ...
logging.basicConfig(level=logging.INFO, format='%(asctime)s | CLIENT | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

SERVER_HTTP_URL = "http://localhost:8000/api/v1/sales"
SERVER_WS_URL_BASE = "ws://localhost:8000/api/v1/sales/ws/voice-chat"
SAMPLE_RATE = 16000
MAX_RECORD_SECONDS = 20
CHANNELS = 1
AUDIO_DTYPE = 'float32'

audio_input_queue = queue.Queue()
stop_recording_event = threading.Event()
playback_queue = queue.Queue()
main_loop_should_exit = asyncio.Event()


# ... (synchronous_record_audio_interactive function remains the same) ...
def synchronous_record_audio_interactive():
    global stop_recording_event
    stop_recording_event.clear()
    recorded_frames = []
    logger.info(f"--- SYNC_REC: Press ENTER to STOP recording (max {MAX_RECORD_SECONDS}s) ---")
    input_thread_active = True
    def callback(indata, frames, time_info, status):
        if status: logger.warning(f"SYNC_REC: Recording status: {status}")
        if not stop_recording_event.is_set():
            recorded_frames.append(indata.copy())
        else: raise sd.CallbackStop
    def listen_for_enter():
        nonlocal input_thread_active
        global stop_recording_event
        try:
            input() 
            if not stop_recording_event.is_set():
                logger.info("SYNC_REC: Enter pressed by user, stopping recording.")
                stop_recording_event.set()
        except EOFError: 
            logger.warning("SYNC_REC: EOFError on input() in listen_for_enter. Setting stop event.")
            if not stop_recording_event.is_set(): stop_recording_event.set()
        except RuntimeError: 
             logger.warning("SYNC_REC: RuntimeError on input() - stdin likely closed. Setting stop event.")
             if not stop_recording_event.is_set(): stop_recording_event.set()
        finally: input_thread_active = False
    input_thread = threading.Thread(target=listen_for_enter, daemon=True)
    input_thread.start()
    stream = None 
    try:
        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=AUDIO_DTYPE, callback=callback)
        with stream: 
            start_time = time.time()
            while not stop_recording_event.is_set() and (time.time() - start_time) < MAX_RECORD_SECONDS:
                if not input_thread.is_alive() and input_thread_active:
                    logger.warning("SYNC_REC: Input listener thread died. Stopping recording.")
                    stop_recording_event.set()
                time.sleep(0.05) 
            if not stop_recording_event.is_set():
                logger.info(f"SYNC_REC: Recording timed out after {MAX_RECORD_SECONDS}s.")
                stop_recording_event.set() 
    except sd.CallbackStop: logger.debug("SYNC_REC: Recording stream stopped via CallbackStop.")
    except Exception as e:
        logger.error(f"SYNC_REC: Error during audio recording: {e}", exc_info=True)
        audio_input_queue.put(None) 
        return
    finally:
        stop_recording_event.set() 
        logger.debug("SYNC_REC: Finished recording attempt.")
    if recorded_frames:
        recording_np = np.concatenate(recorded_frames, axis=0)
        temp_wav_bytes_io = io.BytesIO()
        sf.write(temp_wav_bytes_io, recording_np, SAMPLE_RATE, format='WAV', subtype='PCM_16')
        temp_wav_bytes_io.seek(0)
        audio_bytes_to_send = temp_wav_bytes_io.read()
        audio_input_queue.put(audio_bytes_to_send)
        logger.info(f"SYNC_REC: Audio (len: {len(audio_bytes_to_send)}) added to queue.")
    else:
        logger.warning("SYNC_REC: No audio frames recorded.")
        audio_input_queue.put(b"")

# ... (play_audio_from_queue function remains the same) ...
async def play_audio_from_queue():
    global main_loop_should_exit 
    while not main_loop_should_exit.is_set():
        try:
            audio_bytes = await asyncio.to_thread(playback_queue.get, timeout=0.2)
            if audio_bytes is None: 
                logger.info("Playback thread received explicit stop signal (None).")
                main_loop_should_exit.set() 
                break
            if not audio_bytes: 
                playback_queue.task_done() 
                continue
            logger.info(f"Playing received audio (len: {len(audio_bytes)})")
            try:
                wav_io = io.BytesIO(audio_bytes)
                data, samplerate_from_file = sf.read(wav_io, dtype=AUDIO_DTYPE)
                if samplerate_from_file != SAMPLE_RATE:
                     logger.warning(f"Playback samplerate mismatch: Server sent {samplerate_from_file}Hz, client expects {SAMPLE_RATE}Hz.")
                await asyncio.to_thread(sd.play, data, samplerate_from_file)
                await asyncio.to_thread(sd.wait) 
                logger.info("Finished playing audio.")
            except Exception as e: logger.error(f"Error playing audio: {e}", exc_info=True)
            finally: playback_queue.task_done() 
        except queue.Empty: await asyncio.sleep(0.05) 
        except Exception as e: 
            logger.error(f"Critical error in playback loop: {e}")
            main_loop_should_exit.set() 
            break
    logger.info("Playback loop exited.")


async def voice_chat_client():
    global main_loop_should_exit
    main_loop_should_exit.clear()

    # --- MODIFICATION: Ask for user's name ---
    user_name_for_call = input("Please enter your name for the call: ").strip()
    if not user_name_for_call:
        user_name_for_call = "Valued Customer" # Default if empty
    logger.info(f"Using name: {user_name_for_call}")
    # --- END MODIFICATION ---

    logger.info("Starting a new call with the server...")
    call_id = None
    try:
        http_response = await asyncio.to_thread(
            requests.post,
            f"{SERVER_HTTP_URL}/start-call",
            # --- MODIFICATION: Use the entered name ---
            json={"customer_name": user_name_for_call, "phone_number": "ws-client-001"}
        )
        http_response.raise_for_status()
        response_data = http_response.json()
        call_id = response_data.get("call_id")
        initial_agent_message = response_data.get("first_message")

        if not call_id:
            logger.error("Failed to get call_id from server.")
            return
        logger.info(f"Call started. Call ID: {call_id}")
        logger.info(f"AGENT (initial from HTTP): {initial_agent_message}")

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP Error starting call: {e}")
        if hasattr(e, 'response') and e.response is not None: logger.error(f"Server response: {e.response.text}")
        return
    except Exception as e:
        logger.error(f"Error during HTTP start_call: {e}", exc_info=True)
        return

    uri = f"{SERVER_WS_URL_BASE}/{call_id}"
    logger.info(f"Connecting to WebSocket: {uri}")

    playback_task = asyncio.create_task(play_audio_from_queue())
    receive_task = None
    
    try:
        async with websockets.connect(uri, close_timeout=10) as websocket: # type: ignore
            logger.info("WebSocket connection established.")

            is_connection_active = True 

            async def receive_messages_inner():
                nonlocal is_connection_active # To modify flag in outer scope
                global main_loop_should_exit
                try:
                    async for message in websocket:
                        if main_loop_should_exit.is_set(): break 

                        if isinstance(message, bytes):
                            logger.info(f"Received audio bytes (len:{len(message)}) from server.")
                            playback_queue.put(message)
                        elif isinstance(message, str):
                            try:
                                data = json.loads(message)
                                logger.info(f"Received JSON from server: {data}")
                                msg_type = data.get("type")
                                if msg_type == "user_text":
                                    # Displaying the user's name here would require passing user_name_for_call
                                    # into this scope or fetching it from a shared context if needed.
                                    # For now, just the transcript.
                                    logger.info(f"MY_TRANSCRIPT (from server): {data.get('text')}")
                                elif msg_type == "agent_text":
                                    logger.info(f"AGENT (text fallback): {data.get('text')}")
                                elif msg_type == "error":
                                    logger.error(f"SERVER_ERROR: {data.get('message')}")
                                elif msg_type == "system" and "ended" in data.get("message","").lower():
                                    logger.info(f"SYSTEM: {data.get('message')}")
                                    is_connection_active = False 
                                    main_loop_should_exit.set() 
                                    return 
                            except json.JSONDecodeError:
                                logger.warning(f"Received non-JSON text message: {message}")
                        else:
                            logger.warning(f"Received unexpected message type: {type(message)}")
                except websockets.exceptions.ConnectionClosed: # type: ignore
                    logger.info("WebSocket connection closed during receive loop.")
                    is_connection_active = False
                except Exception as e_recv:
                    logger.error(f"Error in receive_messages_inner: {e_recv}", exc_info=True)
                    is_connection_active = False
                finally:
                    logger.info("Receive loop finished.")
                    main_loop_should_exit.set() 
                    playback_queue.put(None) 

            receive_task = asyncio.create_task(receive_messages_inner())

            while is_connection_active and not main_loop_should_exit.is_set() : # Check both flags
                logger.info("\n>>> Press Enter to START speaking (and Enter again to STOP when done) <<<")
                try:
                    await asyncio.get_event_loop().run_in_executor(None, input) 
                except RuntimeError as e:
                     if "cannot schedule new futures after interpreter shutdown" in str(e) or \
                        "Event loop is closed" in str(e):
                         logger.info("Interpreter or event loop shutting down, exiting send loop.")
                         main_loop_should_exit.set()
                         break
                     raise e
                except EOFError:
                    logger.warning("EOF on input, ending client send loop.")
                    main_loop_should_exit.set()
                    break
                
                if not is_connection_active or main_loop_should_exit.is_set(): break 

                recording_thread = threading.Thread(target=synchronous_record_audio_interactive, daemon=True)
                recording_thread.start()
                
                recorded_audio_bytes = b"" 
                try:
                    recorded_audio_bytes = await asyncio.to_thread(audio_input_queue.get, timeout=MAX_RECORD_SECONDS + 5)
                except queue.Empty:
                    logger.warning("Recording queue timed out. Assuming silence.")
                    stop_recording_event.set() 
                    if recording_thread.is_alive(): recording_thread.join(timeout=1) 
                    recorded_audio_bytes = b"" 
                
                if recording_thread.is_alive(): 
                    logger.debug("Waiting for recording thread to complete...")
                    stop_recording_event.set() 
                    recording_thread.join(timeout=1) 
                    if recording_thread.is_alive():
                        logger.warning("Recording thread did not join as expected.")
                
                if recorded_audio_bytes is None: 
                    logger.error("Recording failed (None received). Ending interaction.")
                    main_loop_should_exit.set()
                    break 
                
                if not is_connection_active or main_loop_should_exit.is_set(): break

                logger.info(f"Sending audio (len: {len(recorded_audio_bytes)}) to server...")
                try:
                    await websocket.send(recorded_audio_bytes) 
                    logger.info("Audio sent.")
                except websockets.exceptions.ConnectionClosed: # type: ignore
                    logger.info("Tried to send but connection was already closed.")
                    is_connection_active = False
                    main_loop_should_exit.set()
                    break
            
            logger.info("Exited main client send loop.")
            if receive_task and not receive_task.done():
                logger.info("Waiting for receive_task to complete after main loop exit...")
                try:
                    await asyncio.wait_for(receive_task, timeout=3.0)
                except asyncio.TimeoutError:
                    logger.warning("Receive task did not complete in time after main loop exit.")
                    if not receive_task.done(): receive_task.cancel()
                except Exception as e_rt_wait:
                     logger.error(f"Error waiting for receive_task: {e_rt_wait}")

    except websockets.exceptions.InvalidURI: # type: ignore
        logger.error(f"Invalid WebSocket URI: {uri}")
    except ConnectionRefusedError:
        logger.error(f"Connection refused for WebSocket URI: {uri}. Is the server running?")
    except websockets.exceptions.ConnectionClosedError as e: # type: ignore
        logger.error(f"WebSocket connection closed with error (likely during connect): {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in client: {e}", exc_info=True)
    finally:
        logger.info("Client shutting down actions...")
        main_loop_should_exit.set() 
        playback_queue.put(None) 
        if 'playback_task' in locals() and playback_task and not playback_task.done(): # type: ignore
            try:
                logger.info("Waiting for playback_task to finish...")
                await asyncio.wait_for(playback_task, timeout=1.0) # type: ignore
            except asyncio.TimeoutError:
                logger.warning("Playback task did not complete in time during shutdown.")
                if not playback_task.done(): playback_task.cancel() # type: ignore
            except Exception as e_pb_final:
                logger.error(f"Error waiting for playback task on final shutdown: {e_pb_final}")
        
        stop_recording_event.set() 
        await asyncio.sleep(0.1) 
        logger.info("Client shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(voice_chat_client())
    except KeyboardInterrupt:
        logger.info("Client terminated by user (Ctrl+C).")
    except Exception as e:
        logger.error(f"Unhandled exception in __main__: {e}", exc_info=True)
    finally:
        logger.info("Application finished.")