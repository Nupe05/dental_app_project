import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from django.core.mail import EmailMessage
from django.conf import settings

from fastai.vision.all import load_learner, PILImage

# === Load the model ONCE ===
MODEL_PATH = os.path.join(settings.BASE_DIR, 'claims', 'abscess_detector.pkl')
abscess_model = load_learner(MODEL_PATH)

def predict_abscess(image_path):
    """Runs prediction on the uploaded x-ray image and returns the label and confidence."""
    try:
        img = PILImage.create(image_path)
        pred, pred_idx, probs = abscess_model.predict(img)
        print(f"[MODEL PREDICTION] {pred} — confidence: {probs[pred_idx]:.4f}")
        return str(pred), float(probs[pred_idx])
    except Exception as e:
        print(f"[MODEL ERROR] {e}")
        return "Error", 0.0


def generate_and_email_claim(recommendation):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 750, "American Dental Association")
    p.setFont("Helvetica", 12)
    p.drawString(200, 730, "Dental Claim Form - Crown Procedure")
    p.line(50, 725, 550, 725)

    p.drawString(50, 700, f"Patient: {recommendation.patient.name}")
    p.drawString(300, 700, f"DOB: {recommendation.patient.dob}")
    p.drawString(50, 680, f"Insurance Provider: {recommendation.patient.insurance_provider}")
    p.drawString(300, 680, f"Policy #: {recommendation.patient.policy_number}")

    p.drawString(50, 650, f"Tooth #: {recommendation.tooth.tooth_number}")
    p.drawString(300, 650, f"CDT Code: {recommendation.cdt_code}")
    p.drawString(50, 630, f"Diagnosis: {recommendation.tooth.diagnosis}")

    p.drawString(50, 610, "Clinical Note:")
    text = p.beginText(50, 595)
    text.setFont("Helvetica", 10)
    for line in recommendation.clinical_note.split("\n"):
        text.textLine(line)
    p.drawText(text)

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
        return "Email sent successfully."
    except Exception as e:
        return f"Failed to send email: {e}"


def generate_and_email_srp_pre_auth(treatment):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 750, "American Dental Association")
    p.setFont("Helvetica", 12)
    p.drawString(180, 730, "Scaling and Root Planing - Pre-Authorization")
    p.line(50, 725, 550, 725)

    p.drawString(50, 700, f"Patient: {treatment.patient.name}")
    p.drawString(300, 700, f"DOB: {treatment.patient.dob}")
    p.drawString(50, 680, f"Insurance Provider: {treatment.patient.insurance_provider}")
    p.drawString(300, 680, f"Policy #: {treatment.patient.policy_number}")

    p.drawString(50, 650, "Procedure: Scaling and Root Planing")
    p.drawString(300, 650, f"CDT Code: {treatment.procedure_code}")
    p.drawString(50, 620, "Clinical Note: Localized 4-5mm pocketing with bleeding on probing")

    # Perio Chart Placeholder
    perio_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'placeholder_periochart.png')
    if os.path.exists(perio_path):
        try:
            perio = ImageReader(perio_path)
            p.drawImage(perio, 50, 460, width=200, height=120)
        except Exception as e:
            p.drawString(50, 480, f"[Perio chart load error: {e}]")
    else:
        p.drawString(50, 480, "[Perio chart not found]")

    # X-ray Placeholder
    xray_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'demo_xray.jpg')
    if os.path.exists(xray_path):
        try:
            xray = ImageReader(xray_path)
            p.drawImage(xray, 300, 460, width=200, height=120)
        except Exception as e:
            p.drawString(300, 480, f"[X-ray load error: {e}]")
    else:
        p.drawString(300, 480, "[X-ray not found]")

    p.showPage()
    p.save()
    buffer.seek(0)

    try:
        email = EmailMessage(
            subject="Scaling & Root Planing Pre-Authorization",
            body="Attached are the documents for SRP pre-authorization, including perio chart and x-ray.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=["damon@dadswag.club"]
        )
        email.attach('srp_pre_auth.pdf', buffer.getvalue(), 'application/pdf')
        email.send()
        return "Email sent successfully."
    except Exception as e:
        return f"Failed to send email: {e}"


def generate_and_email_occlusal_guard_pre_auth(treatment):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 750, "American Dental Association")
    p.setFont("Helvetica", 12)
    p.drawString(180, 730, "Occlusal Guard - Pre-Authorization")
    p.line(50, 725, 550, 725)

    p.drawString(50, 700, f"Patient: {treatment.patient.name}")
    p.drawString(300, 700, f"DOB: {treatment.patient.dob}")
    p.drawString(50, 680, f"Insurance Provider: {treatment.patient.insurance_provider}")
    p.drawString(300, 680, f"Policy #: {treatment.patient.policy_number}")

    p.drawString(50, 650, "Procedure: Occlusal Guard")
    p.drawString(300, 650, f"CDT Code: {treatment.procedure_code}")

    p.drawString(50, 620, "Clinical Note:")
    text = p.beginText(50, 600)
    text.setFont("Helvetica", 10)
    text.textLines("The patient exhibits signs of bruxism and an occlusal guard is recommended.")
    p.drawText(text)

    p.showPage()
    p.save()
    buffer.seek(0)

    try:
        email = EmailMessage(
            subject="Occlusal Guard Pre-Authorization",
            body="Attached is the occlusal guard pre-authorization request.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=["damon@dadswag.club"]
        )
        email.attach('occlusal_guard_pre_auth.pdf', buffer.getvalue(), 'application/pdf')
        email.send()
        return "Email sent successfully."
    except Exception as e:
        return f"Failed to send email: {e}"


def generate_clinical_note(tooth_number, diagnosis):
    return f"Tooth {tooth_number} presents with {diagnosis}. A crown is recommended to restore function and prevent further damage."
