# backend/schemas.py
from typing import List, Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    ticket_id: Optional[int] = None
    history: Optional[List[dict]] = None
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str

class TicketCreate(BaseModel):
    title: str
    description: Optional[str] = ""

class TicketUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    status: Optional[str]

class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    created_at: str
    updated_at: str

