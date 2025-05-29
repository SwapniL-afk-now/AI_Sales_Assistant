# app/prompts/sales_prompts.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage # Added BaseMessage
from app.core.config import settings, logger
from typing import List, Union

# --- Pre-format COURSE_BENEFITS (remains the same logic) ---
try:
    if settings.COURSE_BENEFITS and isinstance(settings.COURSE_BENEFITS, list):
        benefits_with_hyphen = [f"- {benefit}" for benefit in settings.COURSE_BENEFITS]
        FORMATTED_COURSE_BENEFITS_STR = "\n".join(benefits_with_hyphen)
    elif not settings.COURSE_BENEFITS:
        FORMATTED_COURSE_BENEFITS_STR = "- (No specific benefits listed for this course.)"
    else:
        logger.warning("COURSE_BENEFITS is not a list or is None, using default placeholder.")
        FORMATTED_COURSE_BENEFITS_STR = "- (Benefit information unavailable.)"
except Exception as e:
    logger.error(f"Error formatting COURSE_BENEFITS: {e}. Using placeholder.")
    FORMATTED_COURSE_BENEFITS_STR = "- (Error retrieving benefit information.)"

COURSE_DETAILS_FOR_PROMPT = f"""
Course Information:
Course Name: {settings.COURSE_NAME}
Duration: {settings.COURSE_DURATION}
Standard Price: {settings.COURSE_PRICE_FULL}
Special Offer Price: {settings.COURSE_PRICE_SPECIAL}
Key Benefits:
{FORMATTED_COURSE_BENEFITS_STR}
"""

# Qwen specific tokens
IM_START_TOKEN = "<|im_start|>"
IM_END_TOKEN = "<|im_end|>"
SYSTEM_ROLE = "system"
USER_ROLE = "user"
ASSISTANT_ROLE = "assistant"

# --- LangChain ChatPromptTemplate ---
QWEN_SYSTEM_PROMPT_CONTENT = f"""
You are a friendly, professional, and persuasive AI Voice Sales Agent named Alex from Edvantage AI.
Your goal is to pitch our online course, "{settings.COURSE_NAME}", to potential customers over a simulated phone call.
Follow the conversational stages strictly: Introduction, Qualification, Pitch, Objection Handling, and Closing.
Keep your responses concise and natural, like a real human sales agent. Aim for 1-2 sentences per turn unless providing detailed information.
If the customer wants to end the call, or if the conversation reaches a natural conclusion (deal, no deal, follow-up scheduled), include "[END_CALL]" in your response.
Do not generate customer turns or any text after your response. Stop after providing the agent's response. Your response should ONLY be what Alex (the agent) would say.

{COURSE_DETAILS_FOR_PROMPT}

Conversation Stages and Actions:
1.  Introduction: Greet the customer (e.g., "Hi [Customer Name], this is Alex from Edvantage AI...") and state purpose.
2.  Qualification: Ask 2-3 open-ended questions to understand their needs.
3.  Pitch: Present the course, highlighting relevant benefits and the special offer.
4.  Objection Handling: Address concerns empathetically.
5.  Closing: Attempt to schedule a follow-up or get a soft commitment. If not interested, politely end the call.
"""

MAIN_SALES_CHAT_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessage(content=QWEN_SYSTEM_PROMPT_CONTENT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{customer_input}")
])

def format_lc_messages_to_qwen_prompt_string(
    messages: List[BaseMessage] # Expecting a list of BaseMessage instances
) -> str:
    logger.debug(f"format_lc_messages_to_qwen_prompt_string received {len(messages)} messages.")
    prompt_str = ""
    for i, msg in enumerate(messages):
        role = ""
        content_text = "" # Initialize to empty string

        # Ensure msg is a BaseMessage and extract content and role
        if isinstance(msg, SystemMessage):
            role = SYSTEM_ROLE
            content_text = msg.content
        elif isinstance(msg, HumanMessage):
            role = USER_ROLE
            content_text = msg.content
        elif isinstance(msg, AIMessage):
            role = ASSISTANT_ROLE
            content_text = msg.content
        else:
            logger.error(f"Message at index {i} is not a recognized LangChain BaseMessage type. Type: {type(msg)}, Value: {msg}")
            # Optionally, try to infer if it's a dict with 'type' and 'content'
            if hasattr(msg, 'type') and hasattr(msg, 'content'): # Check for attributes directly
                try:
                    msg_type_attr = getattr(msg, 'type')
                    msg_content_attr = getattr(msg, 'content')
                    if isinstance(msg_content_attr, str):
                        content_text = msg_content_attr
                        if msg_type_attr == "system": role = SYSTEM_ROLE
                        elif msg_type_attr == "human": role = USER_ROLE
                        elif msg_type_attr == "ai": role = ASSISTANT_ROLE
                        else:
                            logger.warning(f"Inferred message type '{msg_type_attr}' not standard.")
                            continue # Skip if role can't be determined
                    else:
                        logger.warning(f"Inferred content for message at index {i} is not a string: {type(msg_content_attr)}")
                        continue
                except Exception as e_infer:
                    logger.error(f"Error trying to infer role/content for message at index {i}: {e_infer}")
                    continue
            else:
                continue # Skip this malformed message

        if role and isinstance(content_text, str): # Ensure content is a string after extraction
            prompt_str += f"{IM_START_TOKEN}{role}\n{content_text.strip()}{IM_END_TOKEN}\n"
        elif role and not isinstance(content_text, str): # Should be caught by previous checks, but safeguard
            logger.warning(f"Content of message (role: {role}) at index {i} is not a string: {type(content_text)}")
        elif not role:
            logger.warning(f"Could not determine role for message at index {i}.")


    prompt_str += f"{IM_START_TOKEN}{ASSISTANT_ROLE}\n" # Prompt for assistant's response
    logger.debug(f"Formatted Qwen prompt string (first 200 chars): {prompt_str[:200]}")
    return prompt_str

def get_qwen_initial_greeting_prompt_string(customer_name: str) -> str:
    system_instruction = (
        f"You are Alex, a friendly AI Sales Agent from Edvantage AI. "
        f"Your ONLY task for this turn is to generate the very first opening message for a sales call to a customer named {customer_name}. "
        f"Your output should be ONLY what Alex says, starting directly with Alex's speech. "
        f"The message should introduce yourself, state you are calling about the '{settings.COURSE_NAME}', and ask if it's a good time to talk. "
        f"Example: 'Hi {customer_name}, this is Alex from Edvantage AI. I'm calling to chat briefly about our new {settings.COURSE_NAME}. Is now an okay time to talk for a couple of minutes?'"
    )
    user_instruction = f"The customer's name is {customer_name}. Generate Alex's initial greeting now."

    prompt = (
        f"{IM_START_TOKEN}{SYSTEM_ROLE}\n{system_instruction.strip()}{IM_END_TOKEN}\n"
        f"{IM_START_TOKEN}{USER_ROLE}\n{user_instruction.strip()}{IM_END_TOKEN}\n"
        f"{IM_START_TOKEN}{ASSISTANT_ROLE}\n"
    )
    return prompt