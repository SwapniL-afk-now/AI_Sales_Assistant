# # app/core/conversation_manager.py

# from typing import Dict, Optional, Tuple
# from app.schemas.conversation import CallSession, Utterance
# from app.services.llm_service import get_llm_service, LLMService
# from app.core.config import logger
# import uuid
# from datetime import datetime


# class ConversationManager:
#     def __init__(self):
#         self.active_calls: Dict[str, CallSession] = {}
#         self.llm_service: Optional[LLMService] = get_llm_service()
#         if not self.llm_service or not self.llm_service.is_ready():
#             logger.error("LLM Service not available or not fully initialized in ConversationManager. ConversationManager may not function correctly.")

#     def start_new_call(self, customer_name: str, phone_number: str) -> Tuple[str, str]:
#         if not self.llm_service or not self.llm_service.is_ready():
#             fallback_message = "Hello, our AI system is currently initializing. Please try again shortly."
#             call_id = str(uuid.uuid4())
#             session = CallSession(
#                 call_id=call_id, customer_name=customer_name, phone_number=phone_number, is_active=False
#             )
#             session.add_utterance(speaker="agent", text=fallback_message)
#             self.active_calls[call_id] = session
#             logger.warning(f"LLM service not ready. Started call {call_id} with fallback message.")
#             return call_id, fallback_message

#         call_id = str(uuid.uuid4())
#         session = CallSession(call_id=call_id, customer_name=customer_name, phone_number=phone_number)

#         initial_greeting = self.llm_service.generate_initial_greeting(customer_name) # type: ignore
#         session.add_utterance(speaker="agent", text=initial_greeting)

#         self.active_calls[call_id] = session
#         logger.info(f"New call started. ID: {call_id}, Customer: {customer_name}")
#         return call_id, initial_greeting

#     def process_customer_response(self, call_id: str, customer_message: str) -> Tuple[Optional[str], bool]:
#         if not self.llm_service or not self.llm_service.is_ready():
#              logger.warning("LLM service not ready during process_customer_response.")
#              return "Our AI system is currently having issues. Please try again later.", True

#         session = self.active_calls.get(call_id)
#         if not session or not session.is_active:
#             logger.warning(f"Call ID {call_id} not found or inactive.")
#             return "Call not found or has ended.", True

#         history_before_current_customer_message = session.get_chat_history_for_llm()

#         agent_reply = self.llm_service.generate_response( # type: ignore
#             customer_input=customer_message,
#             chat_history=history_before_current_customer_message
#         )

#         session.add_utterance(speaker="customer", text=customer_message)
#         session.add_utterance(speaker="agent", text=agent_reply)

#         should_end_call = "[END_CALL]" in agent_reply
#         if should_end_call:
#             agent_reply = agent_reply.replace("[END_CALL]", "").strip()
#             session.is_active = False
#             session.end_time = datetime.now()
#             logger.info(f"Call ID {call_id} marked to end by agent.")

#         self.active_calls[call_id] = session
#         return agent_reply, should_end_call

#     def get_conversation_history(self, call_id: str) -> Optional[CallSession]:
#         return self.active_calls.get(call_id)

# conversation_manager_instance: Optional[ConversationManager] = None

# def get_conversation_manager() -> ConversationManager:
#     global conversation_manager_instance
#     if conversation_manager_instance is None:
#         conversation_manager_instance = ConversationManager()
#     return conversation_manager_instance



# app/core/conversation_manager.py

from typing import Dict, Optional, Tuple, List, Any
from app.schemas.conversation import CallSession, Utterance
from app.services.llm_service import get_llm_service, LLMService
from app.core.config import logger
import uuid
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.prompt_values import ChatPromptValue # For type hinting

from app.prompts.sales_prompts import MAIN_SALES_CHAT_PROMPT, format_lc_messages_to_qwen_prompt_string, QWEN_SYSTEM_PROMPT_CONTENT

class ConversationManager:
    def __init__(self):
        self.active_calls: Dict[str, CallSession] = {}
        self.llm_service: Optional[LLMService] = get_llm_service()
        self.sales_chain: Optional[Any] = None

        if not self.llm_service or not self.llm_service.is_ready():
            logger.error("LLM Service not available in ConversationManager. May not function correctly.")
        else:
            langchain_llm_instance = self.llm_service.get_langchain_llm_instance()
            if langchain_llm_instance:
                
                # This function takes the output of MAIN_SALES_CHAT_PROMPT (which is a list of BaseMessage after .format_messages())
                # and converts it into the Qwen-specific string format.
                def lc_messages_to_qwen_string_adapter(messages_list: List[BaseMessage]) -> str:
                    # The `MAIN_SALES_CHAT_PROMPT` already includes the system message.
                    # So, `messages_list` here should be the fully formed list including system, history, and current human.
                    return format_lc_messages_to_qwen_prompt_string(messages_list)

                self.sales_chain = (
                    MAIN_SALES_CHAT_PROMPT # Input: {"chat_history": List[BaseMessage], "customer_input": str}
                                           # Output: ChatPromptValue, which we'll convert to messages
                    | RunnableLambda(lambda prompt_value: prompt_value.to_messages()) # Converts ChatPromptValue to List[BaseMessage]
                    | RunnableLambda(lc_messages_to_qwen_string_adapter) # Converts List[BaseMessage] to Qwen string
                    | langchain_llm_instance  # Input: Qwen-formatted string -> Output: Raw LLM response string
                    | StrOutputParser()       # Input: Raw LLM response string -> Output: Cleaned string
                )
                logger.info("ConversationManager: LCEL sales_chain initialized with corrected formatting steps.")
            else:
                logger.error("ConversationManager: Could not get LangChain LLM instance to build sales_chain.")

    def _convert_session_history_to_lc_messages(self, history: List[Utterance]) -> List[BaseMessage]:
        lc_messages: List[BaseMessage] = []
        for u in history:
            if u.speaker == "agent":
                lc_messages.append(AIMessage(content=u.text))
            else: # customer
                lc_messages.append(HumanMessage(content=u.text))
        return lc_messages

    def start_new_call(self, customer_name: str, phone_number: str) -> Tuple[str, str]:
        if not self.llm_service or not self.llm_service.is_ready():
            fallback_message = "Hello, our AI system is currently initializing. Please try again shortly."
            call_id = str(uuid.uuid4())
            session = CallSession(
                call_id=call_id, customer_name=customer_name, phone_number=phone_number, is_active=False
            )
            session.add_utterance(speaker="agent", text=fallback_message)
            self.active_calls[call_id] = session
            logger.warning(f"LLM service not ready. Started call {call_id} with fallback message.")
            return call_id, fallback_message

        call_id = str(uuid.uuid4())
        session = CallSession(call_id=call_id, customer_name=customer_name, phone_number=phone_number)
        
        initial_greeting = self.llm_service.generate_initial_greeting(customer_name)
        session.add_utterance(speaker="agent", text=initial_greeting) # Add greeting to history

        self.active_calls[call_id] = session
        logger.info(f"New call started. ID: {call_id}, Customer: {customer_name}, Initial Greeting: '{initial_greeting}'")
        return call_id, initial_greeting

    def process_customer_response(self, call_id: str, customer_message: str) -> Tuple[Optional[str], bool]:
        if not self.llm_service or not self.llm_service.is_ready() or not self.sales_chain:
            logger.warning("LLM service not ready or sales_chain not initialized during process_customer_response.")
            return "Our AI system is currently having issues. Please try again later.", True

        session = self.active_calls.get(call_id)
        if not session or not session.is_active:
            logger.warning(f"Call ID {call_id} not found or inactive.")
            return "Call not found or has ended.", True

        chat_history_lc_messages = self._convert_session_history_to_lc_messages(session.history)

        logger.debug(f"Invoking sales_chain for call_id {call_id} with customer_input: '{customer_message}' and history_len: {len(chat_history_lc_messages)}")
        
        agent_reply = "I encountered an issue processing your request." # Default error reply
        should_end_call_due_to_error = True # Assume error means call should end

        try:
            chain_input = {
                "chat_history": chat_history_lc_messages, # This is List[BaseMessage]
                "customer_input": customer_message
            }
            agent_reply_from_chain = self.sales_chain.invoke(chain_input)
            
            if not isinstance(agent_reply_from_chain, str) or not agent_reply_from_chain.strip():
                logger.error(f"Sales chain returned non-string or empty reply: '{agent_reply_from_chain}' (type: {type(agent_reply_from_chain)}). Using fallback.")
                # agent_reply remains the default error message
            else:
                agent_reply = agent_reply_from_chain
                should_end_call_due_to_error = False # Successful chain invocation

        except Exception as e_chain:
            logger.error(f"Error invoking sales_chain for call {call_id}: {e_chain}", exc_info=True)
            # agent_reply remains the default error message, should_end_call_due_to_error remains True

        # Add utterances AFTER LLM processing
        session.add_utterance(speaker="customer", text=customer_message)
        session.add_utterance(speaker="agent", text=agent_reply) # Log the actual reply (could be error or LLM response)

        # Determine if call should end based on LLM instruction OR if an error occurred
        if should_end_call_due_to_error:
            # If an error occurred during chain invocation, we usually want to end the call gracefully.
            session.is_active = False # Mark inactive due to processing error
            session.end_time = datetime.now()
            logger.warning(f"Call ID {call_id} ending due to processing error. Agent reply given: '{agent_reply}'")
            self.active_calls[call_id] = session
            return agent_reply, True
        else:
            # No error, check LLM's instruction
            should_end_call_by_llm = "[END_CALL]" in agent_reply
            if should_end_call_by_llm:
                final_agent_reply = agent_reply.replace("[END_CALL]", "").strip()
                session.is_active = False
                session.end_time = datetime.now()
                logger.info(f"Call ID {call_id} marked to end by agent logic. Final reply: '{final_agent_reply}'")
                self.active_calls[call_id] = session
                return final_agent_reply, True
            else:
                logger.info(f"Call ID {call_id} remains active. Agent reply: '{agent_reply}'")
                self.active_calls[call_id] = session
                return agent_reply, False


    def get_conversation_history(self, call_id: str) -> Optional[CallSession]:
        return self.active_calls.get(call_id)

# Singleton logic for ConversationManager
conversation_manager_instance: Optional[ConversationManager] = None
def get_conversation_manager(recreate_instance: bool = False) -> ConversationManager:
    global conversation_manager_instance
    if recreate_instance or conversation_manager_instance is None:
        logger.info("Creating/Recreating ConversationManager instance.")
        if recreate_instance:
            get_llm_service(recreate_instance=True) # Ensure LLM service is also fresh
        conversation_manager_instance = ConversationManager()
    return conversation_manager_instance