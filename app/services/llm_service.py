# app/services/llm_service.py

from app.core.config import settings, logger
from app.prompts.sales_prompts import (
    # MAIN_SALES_CHAT_PROMPT, # Will be used by the chain in ConversationManager
    format_lc_messages_to_qwen_prompt_string,
    get_qwen_initial_greeting_prompt_string,
    IM_END_TOKEN, # For cleaning
    IM_START_TOKEN, # For cleaning (though less likely needed in output)
    ASSISTANT_ROLE # For cleaning
)
from typing import List, Dict, Optional, Any, Union
import traceback

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models.llms import LLM # Base class for custom LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import Generation, LLMResult

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
    logger.debug("Transformers and torch are available for LocalQwenLLM.")
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    torch = None
    AutoModelForCausalLM, AutoTokenizer = (type(None), type(None))
    logger.warning(f"Transformers library or PyTorch not available. LocalQwenLLM will fail. Error: {e}")

# --- Custom LangChain LLM Wrapper for Local Qwen ---
class LocalQwenLLM(LLM):
    model_id: str = settings.LLM_MODEL_REPO_ID
    tokenizer: Any = None # Will be AutoTokenizer
    model: Any = None     # Will be AutoModelForCausalLM
    device: str = "cpu"   # Default to CPU
    max_new_tokens_generation: int = 180
    max_new_tokens_greeting: int = 100

    # For LangChain's an L C MetaData
    @property
    def _llm_type(self) -> str:
        return "local_qwen_llm_wrapper"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs) # Initialize base LLM class
        if not TRANSFORMERS_AVAILABLE or torch is None:
            raise ImportError("Transformers library or PyTorch is not available. Cannot initialize LocalQwenLLM.")

        logger.info(f"Initializing LocalQwenLLM with model: {self.model_id} on device: {self.device}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
                logger.info(f"Set pad_token_id to eos_token_id ({self.tokenizer.pad_token_id}) for Qwen tokenizer.")

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                device_map=self.device, # Explicitly CPU
                trust_remote_code=True,
                torch_dtype=torch.float32 # Use float32 for CPU
            )
            logger.info(f"LocalQwenLLM: Model {self.model_id} loaded successfully on {self.model.device}.")
        except Exception as e:
            logger.error(f"--- FAILED to initialize LocalQwenLLM model ({self.model_id}) ---", exc_info=True)
            traceback.print_exc()
            raise RuntimeError(f"Could not load local Qwen model: {e}") from e

    def _generate_raw_qwen_response(self, prompt_string: str, max_tokens: int) -> str:
        if not self.model or not self.tokenizer:
            logger.error("LocalQwenLLM: Model or tokenizer not loaded.")
            return "Error: Model not available."
        try:
            inputs = self.tokenizer(prompt_string, return_tensors="pt", padding=True, truncation=False).to(self.model.device)

            eos_token_ids_list = []
            if self.tokenizer.eos_token_id is not None:
                eos_token_ids_list.append(self.tokenizer.eos_token_id)
            im_end_token_id = self.tokenizer.convert_tokens_to_ids(IM_END_TOKEN)
            if im_end_token_id != self.tokenizer.unk_token_id and im_end_token_id not in eos_token_ids_list:
                eos_token_ids_list.append(im_end_token_id)
            final_eos_token_id = eos_token_ids_list if eos_token_ids_list else self.tokenizer.eos_token_id

            output_sequences = self.model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=max_tokens,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=final_eos_token_id,
                do_sample=True, temperature=0.7, top_p=0.8, repetition_penalty=1.05,
            )
            response_text = self.tokenizer.decode(output_sequences[0, inputs["input_ids"].shape[-1]:], skip_special_tokens=False)
            return response_text
        except Exception as e:
            logger.error(f"Error during LocalQwenLLM raw generation:", exc_info=True)
            return "Error during generation."

    def _call(
        self,
        prompt: str, # LangChain's LLM._call expects a single prompt string
        stop: Optional[List[str]] = None, # Stop sequences, though Qwen format handles it
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        # This `prompt` string is expected to be ALREADY FORMATTED in Qwen's specific chat format
        # if this _call method is invoked directly by a simple LangChain chain.
        # The formatting from List[BaseMessage] to Qwen string happens *before* this.
        logger.debug(f"LocalQwenLLM._call received prompt (first 100 chars): {prompt[:100]}")
        raw_response = self._generate_raw_qwen_response(prompt, self.max_new_tokens_generation)
        cleaned_response = self._clean_qwen_response(raw_response, is_greeting=False) # Generic cleaning
        logger.debug(f"LocalQwenLLM._call cleaned response: {cleaned_response}")
        return cleaned_response

    def _clean_qwen_response(self, text: str, is_greeting: bool = False) -> str:
        cleaned_text = text.strip()
        if IM_END_TOKEN in cleaned_text:
            cleaned_text = cleaned_text.split(IM_END_TOKEN, 1)[0].strip()
        if "<|endoftext|>" in cleaned_text:
            cleaned_text = cleaned_text.split("<|endoftext|>", 1)[0].strip()
        assistant_start_marker_full = f"{IM_START_TOKEN}{ASSISTANT_ROLE}\n"
        if cleaned_text.startswith(assistant_start_marker_full):
            cleaned_text = cleaned_text[len(assistant_start_marker_full):].strip()
        if is_greeting and cleaned_text.lower().startswith("alex:"):
            cleaned_text = cleaned_text[len("alex:") :].strip()
        return cleaned_text

    # --- Specific methods for your application, not part of standard LLM interface ---
    def generate_qwen_initial_greeting(self, customer_name: str) -> str:
        prompt_str = get_qwen_initial_greeting_prompt_string(customer_name)
        raw_response = self._generate_raw_qwen_response(prompt_str, self.max_new_tokens_greeting)
        return self._clean_qwen_response(raw_response, is_greeting=True)

# --- LLMService (now a wrapper around the LangChain custom LLM) ---
class LLMService:
    def __init__(self):
        self.llm_mode: str = "None" # Will become "local_qwen_wrapper"
        self.custom_llm: Optional[LocalQwenLLM] = None
        try:
            self.custom_llm = LocalQwenLLM() # Instantiate our LangChain compatible LLM
            self.llm_mode = self.custom_llm._llm_type
            logger.info(f"LLMService initialized with {self.llm_mode}.")
        except Exception as e:
            logger.error(f"LLMService failed to initialize LocalQwenLLM: {e}", exc_info=True)
            self.custom_llm = None # Ensure it's None on failure

    def is_ready(self) -> bool:
        return self.custom_llm is not None and self.custom_llm.model is not None

    def get_langchain_llm_instance(self) -> Optional[LocalQwenLLM]:
        """Returns the underlying LangChain LLM instance for use in LCEL chains."""
        return self.custom_llm

    def generate_initial_greeting(self, customer_name: str) -> str:
        if not self.is_ready() or not self.custom_llm:
            logger.error("LLM not ready for generating initial greeting.")
            return "Hello! Our AI is temporarily unavailable (LLM not ready)."
        return self.custom_llm.generate_qwen_initial_greeting(customer_name)

    def generate_response(self, customer_input: str, chat_history_messages: List[BaseMessage]) -> str:
        """
        Generates a response using the custom LLM.
        Note: This method might be bypassed if ConversationManager uses an LCEL chain directly.
        The chat_history_messages should be a list of BaseMessage (HumanMessage, AIMessage).
        """
        if not self.is_ready() or not self.custom_llm:
            logger.error("LLM not ready for generating response.")
            return "I'm sorry, I'm currently unable to process your request (LLM not ready)."

        # The LCEL chain in ConversationManager will handle prompt formatting.
        # This method is now more of a direct passthrough if called,
        # but ideally, the chain does the work.

        # Construct the full list of messages for Qwen formatting
        # System message is part of MAIN_SALES_CHAT_PROMPT
        from app.prompts.sales_prompts import QWEN_SYSTEM_PROMPT_CONTENT # Get system prompt content
        
        # Create the full message list including the system prompt for qwen formatter
        full_messages_for_qwen_format: List[BaseMessage] = [SystemMessage(content=QWEN_SYSTEM_PROMPT_CONTENT)]
        full_messages_for_qwen_format.extend(chat_history_messages)
        full_messages_for_qwen_format.append(HumanMessage(content=customer_input))

        qwen_prompt_string = format_lc_messages_to_qwen_prompt_string(full_messages_for_qwen_format)
        
        # Directly call the underlying _call or a raw generation method
        # Since _call expects already formatted Qwen string, this is correct.
        return self.custom_llm._call(prompt=qwen_prompt_string)


llm_service_instance: Optional[LLMService] = None
def get_llm_service(recreate_instance: bool = False) -> Optional[LLMService]:
    global llm_service_instance
    if recreate_instance or llm_service_instance is None:
        logger.info(f"Creating/Recreating LLMService instance (with LocalQwenLLM wrapper).")
        llm_service_instance = LLMService()
    return llm_service_instance