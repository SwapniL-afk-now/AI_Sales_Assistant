# test_tts_service.py
import os

def run_tts_tests():
    print("--- Running TTS Service Tests ---")
    try:
        from app.core.config import logger # Initialize logger first
        from app.services.tts_service import get_tts_service, TTSService

        logger.info("Attempting to initialize TTSService...")
        tts = get_tts_service()

        if tts and tts.engine:
            logger.info("SUCCESS: TTSService initialized with pyttsx3 engine.")
        else:
            logger.error("FAILURE: TTSService could not be initialized or engine not available.")
            return

        test_text = "Hello, this is a test of the text to speech synthesis system."
        output_filename = "tts_test_output.wav"

        # Test 1: Synthesize to WAV bytes and save
        logger.info(f"Attempting to synthesize text to '{output_filename}'...")
        audio_bytes = tts.synthesize_to_wav_bytes(test_text, filename=output_filename)

        if audio_bytes and len(audio_bytes) > 0 :
            logger.info(f"SUCCESS: Synthesized audio to bytes (length: {len(audio_bytes)}).")
            # Save the bytes to a file to manually check
            manual_check_filename = "manual_tts_check.wav"
            with open(manual_check_filename, "wb") as f:
                f.write(audio_bytes)
            logger.info(f"  Audio bytes also saved to '{manual_check_filename}' for manual verification.")
            if os.path.exists(output_filename):
                 logger.info(f"  Original temp file '{output_filename}' was likely created and then deleted by the service, which is good.")
            else:
                 # This check depends on the implementation detail of synthesize_to_wav_bytes
                 # If it's meant to leave the file, this is an issue. If it cleans up, this is fine.
                 # My current TTS service code deletes it.
                 logger.info(f"  Temp file '{output_filename}' was not found after synthesis, which is expected if it's cleaned up.")

        else:
            logger.error(f"FAILURE: Failed to synthesize audio to bytes or bytes were empty.")


        # Test 2: Speak locally
        logger.info("\nAttempting to speak text locally...")
        print("  You should HEAR the test sentence now if your speakers are on.")
        success_speak = tts.speak_locally(test_text + " Can you hear me?")
        if success_speak:
            logger.info("SUCCESS: `speak_locally` method executed. Check if you heard audio.")
        else:
            logger.error("FAILURE: `speak_locally` method reported an issue.")

        print("\n--- TTS Service Tests Finished (Check logs and listen for audio) ---")

    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
    except Exception as e:
        print(f"UNEXPECTED ERROR during TTS test: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        from app.core.config import logger
    except ImportError:
        print("Failed to pre-initialize logger.")
    run_tts_tests()