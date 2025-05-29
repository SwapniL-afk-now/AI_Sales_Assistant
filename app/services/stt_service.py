import whisper 
from app.core.config import settings, logger
import os
import tempfile
import numpy as np 
from typing import Optional # Added for type hint

class STTService:
    def __init__(self):
        self.model = None
        try:
            logger.info(f"Loading Whisper STT model: {settings.WHISPER_MODEL_SIZE}")
            self.model = whisper.load_model(settings.WHISPER_MODEL_SIZE)
            logger.info(f"Whisper STT Service initialized with model: {settings.WHISPER_MODEL_SIZE}.")
        except Exception as e:
            logger.error(f"Failed to initialize Whisper STTService: {e}")
            logger.error("Ensure ffmpeg is installed and in PATH. For GPU, ensure CUDA and PyTorch are correctly set up.")
            self.model = None

    def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        if not self.model:
            logger.error("Whisper STT model not available.")
            return "Error: STT service not available."

        logger.info(f"[Whisper STT] Transcribing audio data (length: {len(audio_data)} bytes)")
        
        tmp_audio_file_path = None # Initialize to ensure it's defined for finally block
        try:
            # suffix needs to indicate the audio format if Whisper relies on it.
            # For raw bytes, ensure they are in a format Whisper expects (e.g., WAV).
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio_file: 
                tmp_audio_file.write(audio_data)
                tmp_audio_file_path = tmp_audio_file.name
            
            logger.debug(f"Temporary audio file for Whisper: {tmp_audio_file_path}")
            result = self.model.transcribe(tmp_audio_file_path, fp16=False)
            transcribed_text = result["text"]
            logger.info(f"Whisper STT Result: '{transcribed_text}'")
            return transcribed_text.strip()
        except Exception as e:
            logger.error(f"Error during Whisper STT transcription: {e}")
            return f"Error during transcription: {e}"
        finally:
            if tmp_audio_file_path and os.path.exists(tmp_audio_file_path):
                try:
                    os.remove(tmp_audio_file_path)
                    logger.debug(f"Deleted temporary audio file: {tmp_audio_file_path}")
                except Exception as e_del:
                    logger.error(f"Error deleting temporary audio file {tmp_audio_file_path}: {e_del}")

stt_service_instance: Optional[STTService] = None

def get_stt_service() -> Optional[STTService]:
    global stt_service_instance
    if stt_service_instance is None:
        stt_service_instance = STTService()
    return stt_service_instance