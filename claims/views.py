from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, JsonResponse
from django.core.mail import EmailMessage
from django.conf import settings
from .forms import CrownRecommendationForm
from .models import CrownRecommendation, ToothRecord, Patient, TreatmentRecord
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from django.contrib.auth.decorators import login_required
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

# === Generate and Email Claim PDF ===
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


# === Recommendation Form and PDF Views ===
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
    email_status = generate_and_email_claim(recommendation)
    return render(request, 'claims/recommendation_success.html', {
        'email_status': email_status
    })


# === PMS-style Frontend Views ===
@login_required
def pms_home(request):
    patients = Patient.objects.all()
    return render(request, 'pms/home.html', {'patients': patients})

@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    teeth = ToothRecord.objects.filter(patient=patient)
    return render(request, 'pms/patient_detail.html', {'patient': patient, 'teeth': teeth})

@login_required
def add_crown_treatment(request, patient_id, tooth_id):
    patient = get_object_or_404(Patient, id=patient_id)
    tooth = get_object_or_404(ToothRecord, id=tooth_id)

    if request.method == 'POST':
        TreatmentRecord.objects.create(
            patient=patient,
            tooth=tooth,
            procedure_code='D2740'
        )
        return redirect('pms_success')

    return render(request, 'pms/add_treatment.html', {'patient': patient, 'tooth': tooth})

def pms_success(request):
    return render(request, 'pms/success.html')


# === API Endpoint to Create Treatment ===
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_create_treatment(request):
    data = request.data
    try:
        # FHIR format
        if 'resourceType' in data and data['resourceType'] == 'Procedure':
            patient_id = int(data['subject']['reference'].split('/')[-1])
            tooth_number = int(data['bodySite']['coding'][0]['code'])
            code = data['code']['coding'][0]['code']

        # HL7 format (string-based)
        elif isinstance(data, dict) and 'hl7_raw' in data:
            lines = data['hl7_raw'].splitlines()
            patient_id = None
            tooth_number = None
            code = None
            for line in lines:
                if line.startswith('PID'):
                    patient_id = int(line.split('|')[3])
                elif line.startswith('OBX'):
                    tooth_number = int(line.split('|')[4].split('^')[0])
                elif line.startswith('OBR'):
                    code = line.split('|')[3].split('^')[0]

        # Standard JSON
        else:
            patient_id = data['patient_id']
            tooth_id = data['tooth_id']
            code = data['procedure_code']
            tooth = ToothRecord.objects.get(id=tooth_id)

        patient = Patient.objects.get(id=patient_id)
        if 'tooth' not in locals():
            tooth = ToothRecord.objects.filter(patient=patient, tooth_number=tooth_number).first()
            if not tooth:
                return Response({"error": "Tooth record not found."}, status=status.HTTP_400_BAD_REQUEST)

        record = TreatmentRecord.objects.create(
            patient=patient,
            tooth=tooth,
            procedure_code=code
        )
        return Response({"status": "TreatmentRecord created", "id": record.id}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
