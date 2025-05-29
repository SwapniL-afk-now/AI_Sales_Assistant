# app/core/config.py
import os
import sys

# --- START: Set Hugging Face Cache Directory (MUST BE VERY EARLY) ---
try:
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(current_file_dir)
    project_root_dir = os.path.dirname(app_dir)
    desired_hf_cache_home = os.path.join(project_root_dir, ".huggingface_cache_project")
    if not os.path.exists(desired_hf_cache_home):
        os.makedirs(desired_hf_cache_home, exist_ok=True)
        print(f"[CONFIG_EARLY_SETUP] Hugging Face project cache directory created at: {desired_hf_cache_home}")
    os.environ['HF_HOME'] = desired_hf_cache_home
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    print(f"[CONFIG_EARLY_SETUP] HF_HOME environment variable set to: {os.environ['HF_HOME']}")
except Exception as e_hf_setup:
    print(f"[CONFIG_EARLY_SETUP_ERROR] Error setting up HF_HOME: {e_hf_setup}", file=sys.stderr)
# --- END: Set Hugging Face Cache Directory ---

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import List, Optional
import json
from loguru import logger

dotenv_path_to_check = os.path.join(project_root_dir, '.env')
if os.path.exists(dotenv_path_to_check):
    load_dotenv(dotenv_path_to_check)
else:
    print(f"[CONFIG_WARNING] .env file not found at {dotenv_path_to_check}.", file=sys.stderr)

class Settings(BaseSettings):
    APP_TITLE: str = "AI Voice Sales Agent (Qwen LLM)" # Updated title
    APP_VERSION: str = "0.3.3" # Incremented version
    LOG_LEVEL: str = "INFO"

    HUGGINGFACEHUB_API_TOKEN: Optional[str] = None
    LLM_MODEL_REPO_ID: str = "Qwen/Qwen2-0.5B-Instruct" # <<< CHANGED BACK TO QWEN

    WHISPER_MODEL_SIZE: str = "base"
    COURSE_NAME: str = "AI Mastery Bootcamp"
    COURSE_DURATION: str = "12 weeks"
    COURSE_PRICE_FULL: str = "$499"
    COURSE_PRICE_SPECIAL: str = "$299"
    COURSE_BENEFITS_RAW: str = '["Learn LLMs, Computer Vision, and MLOps", "Hands-on projects", "Job placement assistance", "Certificate upon completion"]'
    HF_EFFECTIVE_CACHE_DIR: Optional[str] = os.environ.get('HF_HOME')

    @property
    def COURSE_BENEFITS(self) -> List[str]:
        try: return json.loads(self.COURSE_BENEFITS_RAW)
        except json.JSONDecodeError:
            error_msg = "[CONFIG_ERROR] Failed to parse COURSE_BENEFITS_RAW."
            try: logger.error(error_msg)
            except NameError: print(error_msg, file=sys.stderr)
            return []

    class Config:
        env_file = dotenv_path_to_check
        env_file_encoding = 'utf-8'
        extra = "ignore"

settings = Settings()

logger.remove()
logger.add(
    sys.stderr, level=settings.LOG_LEVEL.upper(),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

logger.info(f"Effective Hugging Face cache (HF_HOME) is: {settings.HF_EFFECTIVE_CACHE_DIR}")
if settings.HF_EFFECTIVE_CACHE_DIR and project_root_dir and project_root_dir.lower() not in settings.HF_EFFECTIVE_CACHE_DIR.lower():
    logger.warning(f"HF_HOME ('{settings.HF_EFFECTIVE_CACHE_DIR}') not in project root ('{project_root_dir}').")

logger.info(f"{settings.APP_TITLE} Configuration loaded successfully.")
if not settings.HUGGINGFACEHUB_API_TOKEN:
    logger.warning("HUGGINGFACEHUB_API_TOKEN is not set (needed for endpoint mode).")
logger.info(f"Using LLM model (for local or endpoint): {settings.LLM_MODEL_REPO_ID}")
logger.info(f"Using Whisper STT model size: {settings.WHISPER_MODEL_SIZE}")