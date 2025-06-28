from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .forms import CrownRecommendationForm, SRPTreatmentForm
from .models import CrownRecommendation, ToothRecord, Patient, TreatmentRecord
from .utils import generate_and_email_claim, generate_and_email_srp_pre_auth, generate_and_email_occlusal_guard_pre_auth
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.http import FileResponse
from .models import CrownRecommendation
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from .forms import OcclusalGuardForm
from django.shortcuts import render
from .models import Patient, CrownRecommendation, TreatmentRecord
from django.contrib.auth import logout
from django.shortcuts import redirect

from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    template_name = 'claims/login.html'  # We'll create this template next


def custom_logout(request):
    logout(request)
    return redirect('pms_home')


def dashboard(request):
    crown_claims = CrownRecommendation.objects.all().order_by('-submitted_at')
    treatment_claims = TreatmentRecord.objects.all().order_by('-submitted_at')

    return render(request, 'claims/dashboard.html', {
        'crown_claims': crown_claims,
        'treatment_claims': treatment_claims,
    })


def pms_home(request):
    patients = Patient.objects.all()

    # Fetch claims from all models
    crown_claims = CrownRecommendation.objects.exclude(status='Pending')
    other_claims = TreatmentRecord.objects.exclude(status='Pending')

    context = {
        'patients': patients,
        'crown_claims': crown_claims,
        'other_claims': other_claims,
    }
    return render(request, 'pms/dashboard.html', context)



def generate_pdf(request, recommendation_id):
    recommendation = get_object_or_404(CrownRecommendation, id=recommendation_id)
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 750, "American Dental Association")
    p.setFont("Helvetica", 12)
    p.drawString(200, 730, "Dental Claim Summary")

    p.drawString(50, 700, f"Patient: {recommendation.patient.name}")
    p.drawString(300, 700, f"DOB: {recommendation.patient.dob}")
    p.drawString(50, 680, f"Tooth #: {recommendation.tooth.tooth_number}")
    p.drawString(300, 680, f"CDT Code: {recommendation.cdt_code}")
    p.drawString(50, 660, f"Diagnosis: {recommendation.tooth.diagnosis}")
    p.drawString(50, 640, "Clinical Note:")
    
    text = p.beginText(50, 620)
    text.setFont("Helvetica", 10)
    for line in recommendation.clinical_note.splitlines():
        text.textLine(line)
    p.drawText(text)

    p.showPage()
    p.save()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename='claim_summary.pdf')

# === Centralized CDT Codes ===
CDT_CODES = {
    'CROWN': 'D2740',
    'SRP': 'D4341',
    'OCCLUSAL_GUARD': 'D9944',
}

# === Crown Treatment View ===
@login_required
def add_crown_treatment(request, patient_id, tooth_id):
    patient = get_object_or_404(Patient, id=patient_id)
    tooth = get_object_or_404(ToothRecord, id=tooth_id)

    if request.method == 'POST':
        TreatmentRecord.objects.create(
            patient=patient,
            tooth=tooth,
            procedure_code=CDT_CODES['CROWN']
        )
        return redirect('pms_success')

    return render(request, 'pms/add_treatment.html', {'patient': patient, 'tooth': tooth})

# === SRP Treatment View with Quadrant ===
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
            generate_and_email_srp_pre_auth(treatment)
            treatment.mark_submitted()
            return redirect('pms_success')
        else:
            print(form.errors)  # Log the form errors to debug invalid submissions
    else:
        form = SRPTreatmentForm()

    return render(request, 'pms/submit_srp.html', {'form': form, 'patient': patient})
# === Occlusal Guard Auto-Submission View ===
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Patient, ToothRecord, TreatmentRecord
from .utils import generate_and_email_occlusal_guard_pre_auth
from django.contrib.auth.decorators import login_required
from .forms import OcclusalGuardForm  # Ensure this form exists

@login_required
def submit_occlusal_guard(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == 'POST':
        form = OcclusalGuardForm(request.POST)
        if form.is_valid():
            tooth = ToothRecord.objects.filter(patient=patient).first()  # Simplified
            treatment = TreatmentRecord.objects.create(
                patient=patient,
                tooth=tooth,
                procedure_code='D9944'
            )
            treatment.mark_submitted()
            status_msg = generate_and_email_occlusal_guard_pre_auth(treatment)
            print(f"[EMAIL STATUS] {status_msg}")
            messages.success(request, f"Occlusal guard submitted. {status_msg}")
            return redirect('pms_success')
        else:
            print(form.errors)  # 🛠️ For debugging
    else:
        form = OcclusalGuardForm()

    return render(request, 'pms/submit_occlusal_guard.html', {
        'patient': patient,
        'form': form
    })

    
# === PMS Success Page ===
def pms_success(request):
    return render(request, 'pms/success.html')

# === Patient Dashboard View ===
@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    teeth = ToothRecord.objects.filter(patient=patient)
    return render(request, 'pms/patient_detail.html', {'patient': patient, 'teeth': teeth})

# === PMS Home View ===
@login_required
def pms_home(request):
    patients = Patient.objects.all()
    return render(request, 'pms/home.html', {'patients': patients})

# === API Endpoint to Create Treatment Record ===
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

# === Manual Crown Recommendation Form View ===
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

# === Crown Recommendation Success Page ===
def recommendation_success(request):
    return render(request, 'claims/recommendation_success.html')

@login_required
def submit_occlusal_guard(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == 'POST':
        form = OcclusalGuardForm(request.POST)
        if form.is_valid():
            procedure_code = form.cleaned_data['procedure_code']
            # Create dummy tooth record if none selected
            dummy_tooth, _ = ToothRecord.objects.get_or_create(
                patient=patient, tooth_number=99,
                defaults={"diagnosis": "Bruxism", "xray_file": None}
            )
            treatment = TreatmentRecord.objects.create(
                patient=patient,
                tooth=dummy_tooth,
                procedure_code=procedure_code
            )
            return redirect('pms_success')
    else:
        form = OcclusalGuardForm()

    return render(request, 'pms/submit_occlusal_guard.html', {
        'patient': patient,
        'form': form
    })
