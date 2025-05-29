# test_conversation_manager_with_real_llm.py
import traceback

def run_cm_real_llm_tests():
    print("--- Running Conversation Manager Tests (with REAL Local LLM) ---")
    try:
        from app.core.config import logger, settings
        from app.services.llm_service import get_llm_service # Ensure this uses the corrected local LLM
        from app.core.conversation_manager import get_conversation_manager, ConversationManager
        from app.schemas.conversation import Utterance

        # Initialize LLM Service first to ensure it's ready
        logger.info("Initializing LLMService for ConversationManager test...")
        llm = get_llm_service() # Should pick up the working local CPU LLM
        if not llm or not llm.is_ready():
            logger.error("CRITICAL: LLMService is not ready. Cannot proceed with ConversationManager test.")
            print("  Ensure your local LLM (CPU, no quantization) is loading correctly via test_llm_service.py first.")
            return
        logger.info(f"LLMService is ready. Mode: {llm.llm_mode}")

        # Now get/create the ConversationManager
        # It should internally use the already initialized llm_service_instance
        logger.info("Attempting to initialize ConversationManager...")
        manager = get_conversation_manager() # Use the singleton accessor
        
        if not manager:
            logger.error("FAILURE: Could not get ConversationManager instance.")
            return
        if not manager.llm_service or not manager.llm_service.is_ready():
            logger.error(f"FAILURE: ConversationManager's LLM service is not ready or not set. Manager's LLM Mode: {manager.llm_service.llm_mode if manager.llm_service else 'None'}")
            return
        logger.info("SUCCESS: ConversationManager initialized and its LLM service is ready.")


        # Test 1: Start New Call
        customer_name = "Real CM Test User"
        phone_number = "111-222-3333"
        logger.info(f"\nAttempting to start a new call for '{customer_name}'...")
        call_id, first_message = manager.start_new_call(customer_name, phone_number)

        if call_id and first_message and "error" not in first_message.lower() and "unavailable" not in first_message.lower():
            logger.info(f"SUCCESS: New call started. Call ID: {call_id}")
            logger.info(f"  Agent's First Message: '{first_message}'")
        else:
            logger.error(f"FAILURE: start_new_call. Call ID: {call_id}, Message: '{first_message}'")
            return

        # Test 2: Process Customer Response
        customer_message_1 = "Hello, I'd like to know more about your course."
        logger.info(f"\nAttempting to process customer response: '{customer_message_1}'")
        logger.info("(This will involve a real LLM call, may take a moment...)")
        reply_1, should_end_1 = manager.process_customer_response(call_id, customer_message_1)

        if reply_1 and "error" not in reply_1.lower() and "unable" not in reply_1.lower():
            logger.info(f"SUCCESS: Processed response.")
            logger.info(f"  Agent's Reply: '{reply_1}'")
            logger.info(f"  Should End Call: {should_end_1}")
        else:
            logger.error(f"FAILURE: process_customer_response. Reply: '{reply_1}', Should End: {should_end_1}")


        # Test 3: Process another customer response (if call didn't end)
        if not should_end_1:
            customer_message_2 = "That sounds interesting. What's the price?"
            logger.info(f"\nAttempting to process second customer response: '{customer_message_2}'")
            logger.info("(Another real LLM call...)")
            reply_2, should_end_2 = manager.process_customer_response(call_id, customer_message_2)
            if reply_2 and "error" not in reply_2.lower() and "unable" not in reply_2.lower():
                logger.info(f"SUCCESS: Processed second response.")
                logger.info(f"  Agent's Second Reply: '{reply_2}'")
                logger.info(f"  Should End Call (2): {should_end_2}")
            else:
                logger.error(f"FAILURE: process_customer_response (2). Reply: '{reply_2}', Should End: {should_end_2}")
        else:
            logger.info("Skipping second customer response test as call was marked to end.")


        # Test 4: Get Conversation History
        logger.info("\nAttempting to get conversation history...")
        history_session = manager.get_conversation_history(call_id)
        if history_session:
            logger.info(f"SUCCESS: Retrieved conversation history for call ID {call_id}.")
            print(f"  Customer: {history_session.customer_name}, Is Active: {history_session.is_active}")
            print(f"  Number of utterances: {len(history_session.history)}")
            if len(history_session.history) >= 3 : # Agent (greeting), Customer (msg1), Agent (reply1) at minimum
                print(f"  Plausible number of utterances found.")
            else:
                print(f"  WARNING: Utterance count might be lower than expected: {len(history_session.history)}")
            # for utt_idx, utt in enumerate(history_session.history):
            #     print(f"    Utt {utt_idx}: {utt.speaker}: {utt.text[:60]}...") # Print start of each utterance
        else:
            logger.error(f"FAILURE: Could not retrieve conversation history for call ID {call_id}.")


        print("\n--- Conversation Manager (Real LLM) Tests Finished ---")
        print("NOTE: LLM responses will be slow due to CPU execution.")

    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
    except Exception as e:
        print(f"UNEXPECTED ERROR during Conversation Manager test: {e}")
        traceback.print_exc()
    finally:
        # Reset singletons if necessary for subsequent tests or other runs
        try:
            from app.services import llm_service
            if hasattr(llm_service, 'llm_service_instance'):
                llm_service.llm_service_instance = None
                logger.info("Reset llm_service_instance singleton.")
            from app.core import conversation_manager
            if hasattr(conversation_manager, 'conversation_manager_instance'):
                conversation_manager.conversation_manager_instance = None
                logger.info("Reset conversation_manager_instance singleton.")
        except Exception:
            pass # Ignore errors during cleanup


if __name__ == "__main__":
    try:
        from app.core.config import logger # Ensure logger is available
    except ImportError:
        print("Failed to pre-initialize logger from app.core.config.")
    run_cm_real_llm_tests()