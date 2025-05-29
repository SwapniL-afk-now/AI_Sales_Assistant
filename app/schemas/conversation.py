from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
import uuid
from datetime import datetime

class Utterance(BaseModel):
    speaker: Literal["agent", "customer"]
    text: str
    timestamp: datetime = Field(default_factory=datetime.now)

class CallSession(BaseModel):
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_name: str
    phone_number: str
    history: List[Utterance] = []
    current_stage: str = "introduction"
    is_active: bool = True
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    def add_utterance(self, speaker: Literal["agent", "customer"], text: str):
        self.history.append(Utterance(speaker=speaker, text=text))

    def get_chat_history_for_llm(self) -> List[Dict[str, str]]:
        return [{"speaker": u.speaker, "text": u.text} for u in self.history]