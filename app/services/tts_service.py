# app/services/tts_service.py
import pyttsx3
from app.core.config import logger
from typing import Optional
import os

class TTSService:
    def __init__(self):
        self.engine = None
        try:
            self.engine = pyttsx3.init()
            logger.info("TTS Service initialized with pyttsx3.")
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3 TTSService: {e}")
            self.engine = None

    def synthesize_speech(self, text: str) -> Optional[bytes]: # Legacy mock method
        if not self.engine:
            logger.error("pyttsx3 engine not available for TTS.")
            return None
        logger.info(f"[pyttsx3 TTS] Synthesizing (mock): '{text}'")
        try:
            logger.info(f"pyttsx3 would speak: {text}")
            return f"mock_audio_for[{text[:30]}...]".encode('utf-8')
        except Exception as e:
            logger.error(f"Error during pyttsx3 synthesis: {e}")
            return None

    def speak_locally(self, text: str) -> bool:
        if not self.engine:
            logger.error("pyttsx3 engine not available. Cannot speak locally.")
            return False
        try:
            logger.info(f"Attempting to speak locally: '{text}'")
            self.engine.say(text)
            self.engine.runAndWait()
            logger.info("Finished speaking locally.")
            return True
        except Exception as e:
            logger.error(f"Error speaking locally with pyttsx3: {e}")
            return False

    def synthesize_to_wav_bytes(self, text: str, filename: str = "temp_tts_output.wav") -> Optional[bytes]:
        if not self.engine:
            logger.error("pyttsx3 engine not available. Cannot synthesize to WAV.")
            return None
        
        try:
            # Ensure filename is unique enough if multiple requests happen concurrently
            # For simplicity, we'll keep it as is, but in a production system,
            # consider using tempfile.NamedTemporaryFile for the filename.
            # However, pyttsx3 save_to_file needs a string path.
            
            # Ensure any previous file with the same name is gone (important for some OS/pyttsx3 quirks)
            if os.path.exists(filename):
                try: os.remove(filename)
                except Exception: pass


            logger.info(f"Synthesizing to WAV file: '{text}' -> {filename}")
            self.engine.save_to_file(text, filename)
            self.engine.runAndWait() 

            if os.path.exists(filename):
                with open(filename, 'rb') as f:
                    audio_bytes = f.read()
                try:
                    os.remove(filename) 
                except Exception as e_del_after_read:
                    logger.warning(f"Could not remove temp WAV file {filename} after reading: {e_del_after_read}")
                logger.info(f"Successfully synthesized to WAV bytes and cleaned up {filename}.")
                return audio_bytes
            else:
                logger.error(f"Failed to create WAV file {filename} for text: '{text}'")
                return None
        except Exception as e:
            logger.error(f"Error synthesizing to WAV bytes: {e}", exc_info=True)
            if os.path.exists(filename): 
                try:
                    os.remove(filename)
                except Exception as e_del:
                    logger.error(f"Error cleaning up {filename} after synthesis error: {e_del}")
            return None

tts_service_instance: Optional[TTSService] = None

def get_tts_service() -> Optional[TTSService]:
    global tts_service_instance
    if tts_service_instance is None:
        tts_service_instance = TTSService()
    return tts_service_instance