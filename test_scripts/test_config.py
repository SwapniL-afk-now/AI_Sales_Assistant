# test_config.py
import sys
import os

def run_config_tests():
    print("--- Running Configuration Tests ---")
    try:
        # Add project root to Python path to simulate running from root
        # This might be needed if you run this script from a subdirectory later,
        # but for now, assume running from project root.
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        # project_root = os.path.dirname(current_dir) # Adjust if test_config.py is nested
        # sys.path.insert(0, project_root)


        from app.core.config import settings, logger

        print("SUCCESS: Imported 'settings' and 'logger' from app.core.config.")
        logger.info("Logger is working from test_config.py")

        print(f"\nLoaded Settings:")
        print(f"  APP_TITLE: {settings.APP_TITLE}")
        print(f"  APP_VERSION: {settings.APP_VERSION}")
        print(f"  LLM_MODEL_REPO_ID: {settings.LLM_MODEL_REPO_ID}")
        print(f"  WHISPER_MODEL_SIZE: {settings.WHISPER_MODEL_SIZE}")
        print(f"  COURSE_NAME: {settings.COURSE_NAME}")
        print(f"  COURSE_BENEFITS (parsed): {settings.COURSE_BENEFITS}")
        print(f"  HF_EFFECTIVE_CACHE_DIR: {settings.HF_EFFECTIVE_CACHE_DIR}")

        if settings.HF_EFFECTIVE_CACHE_DIR:
            if os.path.exists(settings.HF_EFFECTIVE_CACHE_DIR):
                print(f"  Hugging Face Cache Directory ('{settings.HF_EFFECTIVE_CACHE_DIR}') exists.")
            else:
                print(f"  WARNING: Hugging Face Cache Directory ('{settings.HF_EFFECTIVE_CACHE_DIR}') DOES NOT exist.")
        else:
            print("  WARNING: HF_EFFECTIVE_CACHE_DIR is not set in settings.")


        print("\n--- Configuration Tests Passed ---")

    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
        print("  Ensure you are running this script from the project root directory")
        print("  and your virtual environment is activated with all dependencies.")
        print("  PYTHONPATH:", sys.path)
    except Exception as e:
        print(f"UNEXPECTED ERROR during config test: {e}")

if __name__ == "__main__":
    run_config_tests()