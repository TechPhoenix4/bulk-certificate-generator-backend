import os
from database import SessionLocal
from models import CertificateModel, JobModel
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "./generated_certificates"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_certificate_image(name: str, course: str, cert_id: int) -> str:
  """Generates a certificate image using Pillow and returns the file path."""
  # Create a blank canvas (Landscape A4-ish ratio)
  width, height = 1200, 800
  image = Image.new("RGB", (width, height), color=(255, 255, 250))
  draw = ImageDraw.Draw(image)

  # Draw border decoration
  draw.rectangle([40, 40, width - 40, height - 40], outline=(20, 40, 80), width=5)
  draw.rectangle([50, 50, width - 50, height - 50], outline=(200, 170, 80), width=2)

  try:
    # Fallback to default font if custom fonts are unavailable
    title_font = ImageFont.load_default()
    name_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
  except Exception:
    title_font = name_font = body_font = None

  # Draw text contents
  draw.text((width / 2 - 120, 150), "CERTIFICATE OF COMPLETION", fill=(20, 40, 80))
  draw.text((width / 2 - 80, 280), "This is proudly presented to", fill=(100, 100, 100))
  draw.text((width / 2 - len(name) * 4, 360), name, fill=(20, 20, 20))
  draw.text(
      (width / 2 - 150, 460),
      f"for successfully completing the course: {course}",
      fill=(50, 50, 50),
  )

  file_path = os.path.join(OUTPUT_DIR, f"certificate_{cert_id}.png")
  image.save(file_path)
  return file_path


def process_bulk_certificates_task(job_id: int):
  """Background task processor that handles bulk certificate generation safely."""
  db = SessionLocal()
  try:
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
      return

    job.status = "PROCESSING"
    db.commit()

    certificates = (
        db.query(CertificateModel)
        .filter(CertificateModel.job_id == job_id)
        .all()
    )

    success_count = 0
    failure_count = 0

    for cert in certificates:
      try:
        # Validation simulation / Business logic check
        if not cert.recipient_name or not cert.recipient_email:
          raise ValueError("Missing recipient name or email.")

        # Generate asset
        file_path = generate_certificate_image(
            cert.recipient_name, cert.course_name, cert.id
        )

        cert.file_path = file_path
        cert.status = "SUCCESS"
        success_count += 1
      except Exception as e:
        cert.status = "FAILED"
        cert.error_message = str(e)
        failure_count += 1
      db.commit()

    job.success_count = success_count
    job.failure_count = failure_count
    job.status = "COMPLETED" if failure_count == 0 else "COMPLETED_WITH_ERRORS"
    db.commit()
  except Exception as e:
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if job:
      job.status = "FAILED"
      db.commit()
  finally:
    db.close()