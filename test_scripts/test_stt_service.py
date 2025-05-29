# test_stt_service.py
import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import io
import time
import threading # <--- MOVED 'import threading' TO THE TOP LEVEL

# (The rest of the file remains the same as the previous version I provided)
# ...

def record_live_audio_interactive(sample_rate=16000, filename_to_save=None):
    """
    Records audio until Enter is pressed or a timeout is reached.
    Returns audio bytes or None.
    """
    stop_recording_event = threading.Event() # Now 'threading' is defined
    stop_recording_event.clear()
    recorded_frames = []
    MAX_RECORD_SECONDS_INTERACTIVE = 20

    print(f"\n🎤 Press ENTER to START recording (max {MAX_RECORD_SECONDS_INTERACTIVE}s). Press ENTER again to STOP.")
    try:
        input()
    except EOFError:
        print("EOF on input, cannot start recording.")
        return None
    
    print("Recording... Press ENTER to stop.")

    def callback(indata, frames, time_info, status):
        # Access logger defined in the main scope or passed as an argument
        # For simplicity, assuming logger is globally accessible or not used here
        if status:
            # Using print for direct output in this helper if logger isn't easily accessible
            print(f"Debug: Recording status: {status}")
        if not stop_recording_event.is_set():
            recorded_frames.append(indata.copy())
        else:
            raise sd.CallbackStop

    input_thread_active = True
    def listen_for_enter_to_stop():
        nonlocal input_thread_active
        try:
            input() 
            if not stop_recording_event.is_set():
                print("Enter pressed by user, stopping recording.")
                stop_recording_event.set()
        except EOFError:
            if not stop_recording_event.is_set(): stop_recording_event.set()
        except RuntimeError:
            if not stop_recording_event.is_set(): stop_recording_event.set()
        finally:
            input_thread_active = False

    input_thread = threading.Thread(target=listen_for_enter_to_stop, daemon=True)
    input_thread.start()

    stream = None
    try:
        stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32', callback=callback)
        with stream:
            start_time = time.time()
            while not stop_recording_event.is_set() and (time.time() - start_time) < MAX_RECORD_SECONDS_INTERACTIVE:
                if not input_thread.is_alive() and input_thread_active:
                    print("Input listener thread died. Stopping recording.")
                    stop_recording_event.set()
                time.sleep(0.05)
            
            if not stop_recording_event.is_set():
                print(f"Recording timed out after {MAX_RECORD_SECONDS_INTERACTIVE} seconds.")
                stop_recording_event.set()

    except sd.CallbackStop:
        print("Recording stream stopped via CallbackStop.")
    except Exception as e:
        print(f"Error during audio recording: {e}")
        # If logger is part of app_logger from main test scope
        if 'app_logger' in globals() and hasattr(globals()['app_logger'], 'error'):
            globals()['app_logger'].error(f"Error during audio recording: {e}", exc_info=True)
        return None
    finally:
        stop_recording_event.set()
        # No need to join daemon thread aggressively if it's just listening for input

    if not recorded_frames:
        print("No audio frames were recorded.")
        return None

    print("Processing recorded audio...")
    recording = np.concatenate(recorded_frames, axis=0)
    
    wav_io = io.BytesIO()
    sf.write(wav_io, recording, sample_rate, format='WAV', subtype='PCM_16')
    audio_bytes = wav_io.getvalue()

    if filename_to_save:
        with open(filename_to_save, 'wb') as f:
            f.write(audio_bytes)
        print(f"Live recording saved to {filename_to_save}")
    return audio_bytes


def run_stt_tests():
    print("--- Running STT Service Tests ---")
    # No need for global logger here if app_logger is used directly
    try:
        from app.core.config import logger as app_logger # Use a distinct name

        from app.services.stt_service import get_stt_service

        app_logger.info("Attempting to initialize STTService...")
        stt = get_stt_service()

        if stt and stt.model:
            app_logger.info("SUCCESS: STTService initialized and model loaded.")
        else:
            app_logger.error("FAILURE: STTService could not be initialized or model not loaded.")
            return

        sample_audio_path = "sample_audio.wav" # You can create this file to test
        if os.path.exists(sample_audio_path):
            app_logger.info(f"Attempting to transcribe '{sample_audio_path}'...")
            with open(sample_audio_path, "rb") as f:
                audio_bytes_file = f.read()

            if not audio_bytes_file:
                app_logger.error(f"'{sample_audio_path}' is empty.")
            else:
                transcription_file = stt.transcribe_audio(audio_bytes_file)
                app_logger.info(f"Transcription from file: '{transcription_file}'")
                if transcription_file and "error" not in transcription_file.lower():
                    print(f"  SUCCESS: Transcribed '{sample_audio_path}'")
                else:
                    print(f"  WARNING/FAILURE: Transcription from file: {transcription_file}")
        else:
            app_logger.warning(f"'{sample_audio_path}' not found. Skipping file transcription test.")
            print(f"  INFO: To test with a file, create '{sample_audio_path}' in the project root containing some speech.")

        print("\nAttempting INTERACTIVE live audio recording test...")
        try:
            live_audio_bytes = record_live_audio_interactive(filename_to_save="live_interactive_test_audio.wav")
            
            if live_audio_bytes:
                app_logger.info("Attempting to transcribe live interactive recording...")
                transcription_live = stt.transcribe_audio(live_audio_bytes)
                app_logger.info(f"Transcription from live recording: '{transcription_live}'")
                if transcription_live and "error" not in transcription_live.lower() and len(transcription_live.strip()) > 0:
                    print(f"  SUCCESS: Transcribed live audio: '{transcription_live.strip()}'")
                elif transcription_live and len(transcription_live.strip()) == 0: # Check for empty string AFTER stripping
                    print(f"  INFO: Live audio transcribed as empty. Did you speak clearly and for long enough?")
                else: # Covers None or "Error:"
                    print(f"  WARNING/FAILURE: Transcription from live: {transcription_live}")
            else:
                print("  INFO: No live audio bytes recorded or recording was cancelled/failed.")
        except Exception as e_live:
            app_logger.error(f"Error during live audio recording/transcription section: {e_live}", exc_info=True)
            print("  Make sure you have a working microphone and sounddevice/soundfile dependencies.")


        print("\n--- STT Service Tests Finished (Check logs for details) ---")

    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
    except Exception as e:
        print(f"UNEXPECTED ERROR during STT test: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        # This ensures app.core.config.logger is initialized if it's used by service modules upon their import.
        from app.core.config import logger as app_config_logger 
    except ImportError:
        print("Failed to pre-initialize logger from app.core.config. Service modules might log to stdout if they can't find it.")
    
    run_stt_tests()