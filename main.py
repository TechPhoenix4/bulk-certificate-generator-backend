from database import Base, engine, get_db
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from models import CertificateModel, JobModel
from schemas import JobCreateRequest, JobStatusResponse
from sqlalchemy.orm import Session
from services import process_bulk_certificates_task

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator API",
    description="Backend service for bulk certificate generation and tracking.",
    version="1.0.0",
)


@app.post(
    "/jobs/",
    response_model=JobStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_generation_job(
    payload: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
  if not payload.recipients:
    raise HTTPException(
        status_code=400, detail="Recipients list cannot be empty."
    )

  # Create Job entry
  new_job = JobModel(
      status="PENDING", total_recipients=len(payload.recipients)
  )
  db.add(new_job)
  db.commit()
  db.refresh(new_job)

  # Create individual certificate record placeholders
  for item in payload.recipients:
    cert_record = CertificateModel(
        job_id=new_job.id,
        recipient_name=item.name,
        recipient_email=item.email,
        course_name=item.course_name,
        status="PENDING",
    )
    db.add(cert_record)
  db.commit()
  db.refresh(new_job)

  # Trigger background processing task
  background_tasks.add_task(process_bulk_certificates_task, new_job.id)

  return new_job


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
  job = db.query(JobModel).filter(JobModel.id == job_id).first()
  if not job:
    raise HTTPException(status_code=404, detail="Job not found.")
  return job


@app.get("/certificates/{certificate_id}/download")
def download_certificate(certificate_id: int, db: Session = Depends(get_db)):
  cert = (
      db.query(CertificateModel)
      .filter(CertificateModel.id == certificate_id)
      .first()
  )
  if not cert or not cert.file_path:
    raise HTTPException(
        status_code=404, detail="Certificate file not found or not generated yet."
    )
  return FileResponse(
      cert.file_path, media_type="image/png", filename=f"certificate_{cert.id}.png"
  )