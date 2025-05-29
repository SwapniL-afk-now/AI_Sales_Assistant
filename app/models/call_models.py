from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.conversation import Utterance 

class StartCallRequest(BaseModel):
    phone_number: str = Field(..., example="123-456-7890", min_length=3)
    customer_name: str = Field(..., example="John Doe", min_length=1)

class StartCallResponse(BaseModel):
    call_id: str = Field(..., example="a1b2c3d4-e5f6-7890-1234-567890abcdef")
    first_message: str = Field(..., example="Hi John Doe, this is Alex from Edvantage AI...")

class RespondRequest(BaseModel):
    message: str = Field(..., example="I'm interested, tell me more.", min_length=1)

class RespondResponse(BaseModel):
    reply: str = Field(..., example="Great! Our AI Mastery Bootcamp is a 12-week program...")
    should_end_call: bool = Field(False, example=False)

class ConversationHistoryResponse(BaseModel):
    call_id: str
    customer_name: str
    phone_number: str
    history: List[Utterance]
    is_active: bool
    start_time: str 
    end_time: Optional[str] = None