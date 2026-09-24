from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

class ContactForm(BaseModel):
    name: str = Field(..., min_length=2, max_length=80, description="Sender's full name")
    email: EmailStr = Field(..., description="Valid email address")
    subject: str = Field(..., min_length=1, max_length=120, description="Subject of the message")
    message: str = Field(..., min_length=10, max_length=2000, description="Message body")
    website: Optional[str] = Field(default=None, description="Honeypot field for spam prevention")

class ContactResponse(BaseModel):
    status: str
    message: str

class MessageRecord(BaseModel):
    id: int
    name: str
    email: str
    subject: str
    message: str
    created_at: str
    ip_hash: str
