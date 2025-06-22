from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse
from django.core.mail import EmailMessage
from django.conf import settings
from .forms import CrownRecommendationForm
from .models import CrownRecommendation
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader


def create_crown_recommendation(request):
    if request.method == 'POST':
        form = CrownRecommendationForm(request.POST)
        if form.is_valid():
            recommendation = form.save()
            return redirect('generate_pdf', recommendation_id=recommendation.id)
    else:
        form = CrownRecommendationForm()
    return render(request, 'claims/recommendation_form.html', {'form': form})


def recommendation_success(request):
    return render(request, 'claims/recommendation_success.html')


def generate_pdf(request, recommendation_id):
    recommendation = get_object_or_404(CrownRecommendation, id=recommendation_id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # ADA-style header
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

    # Tooth and Procedure info
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

    # X-ray image (if available)
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

    # Send email to staff with the PDF attached
    try:
        email = EmailMessage(
            subject="New Crown Claim Submission",
            body="Please find the attached crown insurance claim.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=["damon@test.com"]
        )
        email.attach('crown_claim.pdf', buffer.getvalue(), 'application/pdf')
        email.send()
        email_status = "Email sent successfully to damon@test.com."
    except Exception as e:
        email_status = f"Failed to send email: {e}"

    return render(request, 'claims/recommendation_success.html', {
        'email_status': email_status
    })
