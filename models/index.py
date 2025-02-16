from pydantic import BaseModel

class ChatMessage(BaseModel):
    question: str