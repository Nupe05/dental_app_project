from django.core.mail import EmailMessage
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import io
import os

# === Generate Crown Claim PDF and Email ===
def generate_and_email_claim(recommendation):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # ADA header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 750, "American Dental Association")
    p.setFont("Helvetica", 12)
    p.drawString(200, 730, "Dental Claim Form - Crown Procedure")
    p.line(50, 725, 550, 725)

    # Patient info
    p.drawString(50, 700, f"Patient: {recommendation.patient.name}")
    p.drawString(300, 700, f"DOB: {recommendation.patient.dob}")
    p.drawString(50, 680, f"Insurance Provider: {recommendation.patient.insurance_provider}")
    p.drawString(300, 680, f"Policy #: {recommendation.patient.policy_number}")

    # Tooth info
    p.drawString(50, 650, f"Tooth #: {recommendation.tooth.tooth_number}")
    p.drawString(300, 650, f"CDT Code: {recommendation.cdt_code}")
    p.drawString(50, 630, f"Diagnosis: {recommendation.tooth.diagnosis}")

    # Clinical Note
    p.drawString(50, 610, "Clinical Note:")
    text = p.beginText(50, 595)
    text.setFont("Helvetica", 10)
    for line in recommendation.clinical_note.split("\n"):
        text.textLine(line)
    p.drawText(text)

    # X-ray image
    if recommendation.tooth.xray_file:
        try:
            xray_path = recommendation.tooth.xray_file.path
            xray = ImageReader(xray_path)
            p.drawImage(xray, 350, 500, width=150, height=150, preserveAspectRatio=True)
        except Exception as e:
            p.drawString(50, 480, f"[X-ray could not be loaded: {e}]")

    p.showPage()
    p.save()
    buffer.seek(0)

    try:
        email = EmailMessage(
            subject="New Crown Claim Submission",
            body="Please find the attached crown insurance claim.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=["damon@dadswag.club"]
        )
        email.attach('crown_claim.pdf', buffer.getvalue(), 'application/pdf')
        email.send()
        return "Email sent successfully to damon@dadswag.club."
    except Exception as e:
        return f"Failed to send email: {e}"

# === Generate SRP Pre-Auth PDF and Email ===
def generate_and_email_srp_pre_auth(treatment):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # ADA-style header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 750, "American Dental Association")
    p.setFont("Helvetica", 12)
    p.drawString(180, 730, "Scaling and Root Planing - Pre-Authorization")
    p.line(50, 725, 550, 725)

    # Patient info
    p.drawString(50, 700, f"Patient: {treatment.patient.name}")
    p.drawString(300, 700, f"DOB: {treatment.patient.dob}")
    p.drawString(50, 680, f"Insurance Provider: {treatment.patient.insurance_provider}")
    p.drawString(300, 680, f"Policy #: {treatment.patient.policy_number}")

    # Procedure info
    p.drawString(50, 650, "Procedure: Scaling and Root Planing")
    p.drawString(300, 650, f"CDT Code: {treatment.procedure_code}")
    quadrant = getattr(treatment, 'quadrant', 'Not specified')
    p.drawString(50, 630, f"Quadrant: {quadrant}")

    # Simulated Perio Chart
    p.drawString(50, 600, "Attached: Most Recent Perio Chart")
    p.rect(50, 540, 200, 40)
    p.drawString(55, 560, "Pocket depths: 4-5mm localized")
    p.drawString(55, 545, "Bleeding: Present")

    # Simulated X-ray image
    xray_path = os.path.join(settings.BASE_DIR, 'static', 'demo_xray.jpg')
    if os.path.exists(xray_path):
        try:
            xray = ImageReader(xray_path)
            p.drawImage(xray, 300, 520, width=200, height=150, preserveAspectRatio=True)
        except Exception as e:
            p.drawString(300, 500, f"[X-ray load error: {e}]")
    else:
        p.drawString(300, 500, "[Demo X-ray not found: demo_xray.jpg]")

    p.showPage()
    p.save()
    buffer.seek(0)

    try:
        email = EmailMessage(
            subject="Scaling & Root Planing Pre-Authorization",
            body="Attached are the necessary documents for pre-authorization.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=["damon@dadswag.club"]
        )
        email.attach('srp_pre_auth.pdf', buffer.getvalue(), 'application/pdf')
        email.send()
        return "Email sent successfully to damon@dadswag.club."
    except Exception as e:
        return f"Failed to send email: {e}"

# === Generate Clinical Note for Crown ===
def generate_clinical_note(tooth_number, diagnosis):
    return f"Tooth #{tooth_number} shows {diagnosis}. Crown recommended to restore function and prevent further structural compromise."
