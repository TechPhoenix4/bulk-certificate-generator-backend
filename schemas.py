from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class Recipient(BaseModel):
  name: str
  email: EmailStr
  course_name: str


class JobCreateRequest(BaseModel):
  recipients: List[Recipient]


class CertificateResponse(BaseModel):
  id: int
  recipient_name: str
  recipient_email: str
  course_name: str
  status: str
  error_message: Optional[str] = None
  file_path: Optional[str] = None

  class Config:
    from_attributes = True


class JobStatusResponse(BaseModel):
  id: int
  status: str
  total_recipients: int
  success_count: int
  failure_count: int
  created_at: datetime
  certificates: List[CertificateResponse] = []

  class Config:
    from_attributes = True