from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone

from .forms import (
    CrownRecommendationForm,
    SRPTreatmentForm,
    OcclusalGuardForm,
    PatientXRayForm
)
from .models import (
    Patient,
    ToothRecord,
    CrownRecommendation,
    TreatmentRecord,
    PatientXRay
)
from .utils import (
    generate_and_email_claim,
    generate_and_email_srp_pre_auth,
    generate_and_email_occlusal_guard_pre_auth,
    predict_abscess,
    mock_submit_insurance_claim
)

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

# === Authentication Views ===
class CustomLoginView(LoginView):
    template_name = 'claims/login.html'

def custom_logout(request):
    logout(request)
    return redirect('pms_home')

# === Home & Dashboard ===
@login_required
def pms_home(request):
    patients = Patient.objects.all()
    return render(request, 'pms/home.html', {'patients': patients})

@login_required
def dashboard(request):
    crown_claims = CrownRecommendation.objects.all().order_by('-submitted_at')
    treatment_claims = TreatmentRecord.objects.all().order_by('-submitted_at')
    return render(request, 'claims/dashboard.html', {
        'crown_claims': crown_claims,
        'treatment_claims': treatment_claims,
    })

# === Patient Views ===
@login_required
def patient_list(request):
    patients = Patient.objects.all()
    return render(request, 'pms/patient_list.html', {'patients': patients})

@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    teeth = ToothRecord.objects.filter(patient=patient)
    return render(request, 'pms/patient_detail.html', {'patient': patient, 'teeth': teeth})

# === X-ray Upload ===
@login_required
def take_xray(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    if request.method == 'POST':
        form = PatientXRayForm(request.POST, request.FILES)
        if form.is_valid():
            xray = form.save(commit=False)
            xray.patient = patient
            xray.save()
            messages.success(request, "X-ray uploaded successfully.")
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = PatientXRayForm()
    return render(request, 'pms/take_xray.html', {'patient': patient, 'form': form})

# === AI-Assisted Crown Submission ===
@login_required
def add_crown_treatment(request, patient_id, tooth_id):
    patient = get_object_or_404(Patient, id=patient_id)
    tooth = get_object_or_404(ToothRecord, id=tooth_id)
    latest_xray = patient.patientxray_set.order_by('-uploaded_at').first()

    if request.method == 'POST':
        diagnosis = "Healthy Tooth"
        clinical_note = "Tooth is healthy and a crown isn't necessary."

        if latest_xray:
            pred, prob = predict_abscess(latest_xray.image.path)
            if pred.lower() == 'abscessed':
                diagnosis = "Abscess detected"
                clinical_note = "X-ray shows evidence of a periapical abscess. Root canal recommended. Crown required post-treatment."

        tooth.diagnosis = diagnosis
        tooth.xray_file = latest_xray.image if latest_xray else None
        tooth.save()

        recommendation = CrownRecommendation.objects.create(
            patient=patient,
            tooth=tooth,
            clinical_note=clinical_note
        )
        recommendation.mark_submitted()
        generate_and_email_claim(recommendation)
        mock_submit_insurance_claim(recommendation)

        return redirect('pms_success')

    return render(request, 'pms/add_treatment.html', {'patient': patient, 'tooth': tooth})

# === Occlusal Guard Submission ===
@login_required
def submit_occlusal_guard(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == 'POST':
        form = OcclusalGuardForm(request.POST, patient=patient)
        if form.is_valid():
            tooth = form.cleaned_data['tooth']
            treatment = TreatmentRecord.objects.create(
                patient=patient,
                tooth=tooth,
                procedure_code='D9944'
            )
            treatment.mark_submitted()
            generate_and_email_occlusal_guard_pre_auth(treatment)
            mock_submit_insurance_claim(treatment)
            return redirect('pms_success')
    else:
        form = OcclusalGuardForm(patient=patient)

    return render(request, 'pms/submit_occlusal_guard.html', {'patient': patient, 'form': form})

# === SRP Submission ===
@login_required
def submit_srp_treatment(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == 'POST':
        form = SRPTreatmentForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['procedure_code']
            tooth_number = form.cleaned_data['tooth_number']
            quadrant = form.cleaned_data['quadrant']

            tooth = ToothRecord.objects.filter(patient=patient, tooth_number=int(tooth_number)).first()
            if not tooth:
                return JsonResponse({"error": "Tooth record not found."}, status=400)

            treatment = TreatmentRecord.objects.create(
                patient=patient,
                tooth=tooth,
                procedure_code=code,
                quadrant=quadrant
            )
            treatment.mark_submitted()
            generate_and_email_srp_pre_auth(treatment)
            mock_submit_insurance_claim(treatment)
            return redirect('pms_success')
    else:
        form = SRPTreatmentForm()

    return render(request, 'pms/submit_srp.html', {'form': form, 'patient': patient})

# === Success Page ===
def pms_success(request):
    return render(request, 'pms/success.html')

# === Manual Crown Entry ===
@login_required
def create_crown_recommendation(request):
    if request.method == 'POST':
        form = CrownRecommendationForm(request.POST, request.FILES)
        if form.is_valid():
            recommendation = form.save()
            generate_and_email_claim(recommendation)
            return redirect('recommendation_success')
    else:
        form = CrownRecommendationForm()
    return render(request, 'claims/recommendation_form.html', {'form': form})

def recommendation_success(request):
    return render(request, 'claims/recommendation_success.html')

# === PDF Generation ===
def generate_crown_pdf(request, recommendation_id):
    claim = get_object_or_404(CrownRecommendation, id=recommendation_id)
    return _build_pdf_response(claim.patient.name, claim.patient.dob, claim.tooth.tooth_number,
                                claim.cdt_code, claim.tooth.diagnosis, claim.clinical_note, "crown_summary.pdf")

def generate_treatment_pdf(request, treatment_id):
    treatment = get_object_or_404(TreatmentRecord, id=treatment_id)
    diagnosis = treatment.tooth.diagnosis if treatment.tooth else "N/A"
    note = f"Pre-authorization request for {treatment.procedure_code}."
    return _build_pdf_response(treatment.patient.name, treatment.patient.dob,
                                treatment.tooth.tooth_number if treatment.tooth else "-",
                                treatment.procedure_code, diagnosis, note, "treatment_summary.pdf")

def _build_pdf_response(patient_name, dob, tooth_num, cdt, diagnosis, note, filename):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 750, "American Dental Association")
    p.setFont("Helvetica", 12)
    p.drawString(200, 730, "Dental Claim Summary")

    p.drawString(50, 700, f"Patient: {patient_name}")
    p.drawString(300, 700, f"DOB: {dob}")
    p.drawString(50, 680, f"Tooth #: {tooth_num}")
    p.drawString(300, 680, f"CDT Code: {cdt}")
    p.drawString(50, 660, f"Diagnosis: {diagnosis}")
    p.drawString(50, 640, "Clinical Note:")

    text = p.beginText(50, 620)
    text.setFont("Helvetica", 10)
    for line in note.splitlines():
        text.textLine(line)
    p.drawText(text)

    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=filename)

# === External API ===
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_create_treatment(request):
    data = request.data
    try:
        patient_id = data['patient_id']
        tooth_id = data['tooth_id']
        code = data['procedure_code']

        patient = Patient.objects.get(id=patient_id)
        tooth = ToothRecord.objects.get(id=tooth_id)

        record = TreatmentRecord.objects.create(
            patient=patient,
            tooth=tooth,
            procedure_code=code
        )
        return Response({"status": "TreatmentRecord created", "id": record.id}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# === Test Endpoint ===
@login_required
def test_model_view(request, patient_id):
    xray = PatientXRay.objects.filter(patient_id=patient_id).last()
    if not xray:
        return HttpResponse("No x-ray found for this patient.")
    pred, prob = predict_abscess(xray.image.path)
    return HttpResponse(f"Model result: {pred} (Confidence: {prob:.2%})")
