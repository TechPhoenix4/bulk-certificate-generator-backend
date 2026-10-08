from datetime import datetime
from database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class JobModel(Base):
  __tablename__ = "jobs"

  id = Column(Integer, primary_key=True, index=True)
  status = Column(
      String, default="PENDING"
  )  # PENDING, PROCESSING, COMPLETED, FAILED
  total_recipients = Column(Integer, default=0)
  success_count = Column(Integer, default=0)
  failure_count = Column(Integer, default=0)
  created_at = Column(DateTime, default=datetime.utcnow)

  certificates = relationship(
      "CertificateModel", back_populates="job", cascade="all, delete-orphan"
  )


class CertificateModel(Base):
  __tablename__ = "certificates"

  id = Column(Integer, primary_key=True, index=True)
  job_id = Column(Integer, ForeignKey("jobs.id"))
  recipient_name = Column(String, index=True)
  recipient_email = Column(String)
  course_name = Column(String)
  status = Column(String, default="PENDING")  # SUCCESS, FAILED
  error_message = Column(Text, nullable=True)
  file_path = Column(String, nullable=True)
  created_at = Column(DateTime, default=datetime.utcnow)

  job = relationship("JobModel", back_populates="certificates")