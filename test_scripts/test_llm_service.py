# # test_llm_service.py
# import traceback

# def run_llm_tests():
#     print("--- Running LLM Service Tests (Local LLM Only) ---")
#     try:
#         from app.core.config import logger, settings
#         from app.services.llm_service import get_llm_service, LLMService

#         logger.info(f"Attempting to initialize LLMService. Configured model: {settings.LLM_MODEL_REPO_ID}")
#         llm = get_llm_service()

#         if not llm:
#             logger.error("CRITICAL FAILURE: LLMService object could not be created by get_llm_service().")
#             return

#         # Updated readiness check for new mode name
#         if llm.is_ready() and ("local" in llm.llm_mode): # Check if mode contains "local"
#             logger.info(f"SUCCESS: LLMService initialized and ready. Mode: {llm.llm_mode}")
#             if "no_quant" in llm.llm_mode:
#                 logger.info("  LLM is running on CPU without bitsandbytes quantization.")
#         else:
#             logger.error(f"FAILURE: LLMService is not ready. Mode: {llm.llm_mode}.")
#             logger.error("  This means local LLM initialization failed. Review the detailed error messages above this line from LLMService.__init__.")
#             print("    " + "="*60)
#             print("    IMPORTANT: Local LLM FAILED TO LOAD. Check console for detailed traceback.")
#             # ... (rest of the error message) ...
#             print("    " + "="*60)
#             return

#         # ... (rest of the test script: Test 1 and Test 2 for greeting/response generation) ...
#         # Test 1: Generate Initial Greeting
#         customer_name = "Test Customer"
#         logger.info(f"\nAttempting to generate initial greeting for '{customer_name}'...")
#         greeting = llm.generate_initial_greeting(customer_name)
#         logger.info(f"Generated Greeting: {greeting}")

#         is_greeting_error = "error" in greeting.lower() or \
#                             "unavailable" in greeting.lower() or \
#                             "fallback" in greeting.lower() or \
#                             not greeting.strip()

#         if greeting and not is_greeting_error and len(greeting) > 10:
#             print(f"  SUCCESS: Generated a plausible initial greeting.")
#         else:
#             print(f"  WARNING/FAILURE: Greeting seems off, is an error message, or empty: '{greeting}'")


#         # Test 2: Generate Response
#         history_greeting = greeting if greeting and not is_greeting_error else f"Hi {customer_name}, this is Alex from Sales."

#         chat_history_for_test = [
#             {"speaker": "agent", "text": history_greeting},
#             {"speaker": "customer", "text": "Hello, I'm interested in learning more about your offers."}
#         ]

#         customer_input = "What is the main product you are selling?"
#         logger.info(f"\nAttempting to generate response to: '{customer_input}'")
#         logger.info(f"With history (agent's last): {history_greeting}")

#         response = llm.generate_response(customer_input=customer_input, chat_history=chat_history_for_test)
#         logger.info(f"Generated Response: {response}")

#         is_response_error = "error" in response.lower() or \
#                             "unable" in response.lower() or \
#                             "fallback" in response.lower() or \
#                             not response.strip()

#         if response and not is_response_error and len(response) > 10:
#             print(f"  SUCCESS: Generated a plausible response.")
#             if "[END_CALL]" in response:
#                 print("  INFO: Response contains [END_CALL] tag (raw LLM output).")
#         else:
#             print(f"  WARNING/FAILURE: Response seems off, is an error message, or empty: '{response}'")


#         print("\n--- LLM Service Tests Finished (Check logs for details) ---")


#     except ImportError as e:
#         print(f"IMPORT ERROR: {e}")
#         print("  Ensure you are running this script from the project root directory")
#         print("  and your virtual environment is activated with all dependencies.")
#     except Exception as e:
#         print(f"UNEXPECTED ERROR during LLM test: {e}")
#         traceback.print_exc()


# if __name__ == "__main__":
#     try:
#         from app.core.config import logger
#     except ImportError:
#         print("Failed to pre-initialize logger. Ensure app.core.config is accessible.")
#     run_llm_tests()


# test_llm_service.py
import traceback
from typing import List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

def run_llm_tests():
    print("--- Running LLM Service Tests (with LocalQwenLLM LangChain Wrapper) ---")
    try:
        import torch
        from app.core.config import logger, settings
        from app.services.llm_service import get_llm_service, LLMService, LocalQwenLLM # Import LocalQwenLLM too
        from app.prompts.sales_prompts import MAIN_SALES_CHAT_PROMPT, format_lc_messages_to_qwen_prompt_string

        logger.info(f"Attempting to initialize LLMService (which wraps LocalQwenLLM). Model: {settings.LLM_MODEL_REPO_ID}")
        llm_service = get_llm_service()

        if not llm_service or not llm_service.is_ready() or not llm_service.custom_llm:
            logger.error("CRITICAL FAILURE: LLMService or its LocalQwenLLM instance could not be initialized or is not ready.")
            print("  Check previous logs for errors during LocalQwenLLM initialization (e.g., model loading).")
            return
        
        local_qwen_llm_instance = llm_service.custom_llm
        logger.info(f"SUCCESS: LLMService initialized. Wrapped LLM type: {local_qwen_llm_instance._llm_type}, Model device: {local_qwen_llm_instance.model.device}")
        print(f"  ==> LLM is running on device: {local_qwen_llm_instance.model.device} <==")

        # Test 1: Generate Initial Greeting (using LLMService's direct method)
        customer_name = "LangChain Test User"
        logger.info(f"\nTesting initial greeting for '{customer_name}' via LLMService method...")
        greeting = llm_service.generate_initial_greeting(customer_name)
        logger.info(f"Generated Greeting: {greeting}")
        is_greeting_error = "error" in greeting.lower() or "unavailable" in greeting.lower() or not greeting.strip()
        if greeting and not is_greeting_error and len(greeting) > 10:
            print(f"  SUCCESS: Greeting generation via LLMService method seems OK.")
        else:
            print(f"  WARNING/FAILURE: Greeting via LLMService method: '{greeting}'")

        # Test 2: Test the LocalQwenLLM wrapper directly with a Qwen-formatted prompt string
        logger.info(f"\nTesting LocalQwenLLM._call directly with a pre-formatted Qwen string...")
        # Create a minimal Qwen prompt string for a simple test
        simple_qwen_prompt = format_lc_messages_to_qwen_prompt_string([
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="What is 2+2?")
        ])
        direct_response = local_qwen_llm_instance._call(prompt=simple_qwen_prompt) # type: ignore
        logger.info(f"Direct call response: {direct_response}")
        if direct_response and "error" not in direct_response.lower() and "4" in direct_response: # Expecting "4"
            print(f"  SUCCESS: LocalQwenLLM._call with pre-formatted string worked.")
        else:
            print(f"  WARNING/FAILURE: Direct call response: '{direct_response}'")


        # Test 3: Test conversation response generation via LLMService's method
        # This method now internally formats to Qwen string and calls the LocalQwenLLM
        logger.info(f"\nTesting conversational response via LLMService.generate_response...")
        history_for_llm_service: List[BaseMessage] = [
            AIMessage(content=greeting if greeting and not is_greeting_error else "Hi there!"),
            HumanMessage(content="Tell me about the course.")
        ]
        customer_input_2 = "What is the price?"
        
        response_2 = llm_service.generate_response(
            customer_input=customer_input_2,
            chat_history_messages=history_for_llm_service
        )
        logger.info(f"LLMService.generate_response output: {response_2}")
        is_response_2_error = "error" in response_2.lower() or "unable" in response_2.lower() or not response_2.strip()
        if response_2 and not is_response_2_error and len(response_2) > 10:
            print(f"  SUCCESS: LLMService.generate_response seems OK.")
        else:
            print(f"  WARNING/FAILURE: LLMService.generate_response: '{response_2}'")


        print("\n--- LLM Service (LangChain Wrapper) Tests Finished ---")
        print("NOTE: LLM responses will be slow due to CPU execution.")

    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
    except Exception as e:
        print(f"UNEXPECTED ERROR during LLM test: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        from app.core.config import logger
    except ImportError:
        print("Failed to pre-initialize logger. Ensure app.core.config is accessible.")
    run_llm_tests()