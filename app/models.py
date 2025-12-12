from pydantic import BaseModel

class SendRequest(BaseModel):
    content: str

class DeliverMessage(BaseModel):
    message_id: str
    sender_id: int
    timestamp: int
    content: str

class AckMessage(BaseModel):
    message_id: str
    sender_id: int
    receiver_id: int

class DelayConfig(BaseModel):
    message_id: str
    delay_ms: int
