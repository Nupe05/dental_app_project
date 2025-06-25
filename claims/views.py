from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .forms import CrownRecommendationForm, SRPTreatmentForm
from .models import CrownRecommendation, ToothRecord, Patient, TreatmentRecord
from .utils import generate_and_email_claim, generate_and_email_srp_pre_auth
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

# === Centralized CDT Codes ===
CDT_CODES = {
    'CROWN': 'D2740',
    'SRP': 'D4341',
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

## === SRP Treatment View with Quadrant ===
@login_required
def submit_srp_treatment(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == 'POST':
        form = SRPTreatmentForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['procedure_code']
            tooth_number = form.cleaned_data['tooth_number']
            quadrant = form.cleaned_data['quadrant']

            tooth = ToothRecord.objects.filter(patient=patient, tooth_number=tooth_number).first()
            if not tooth:
                return JsonResponse({"error": "Tooth record not found."}, status=400)

            treatment = TreatmentRecord.objects.create(
                patient=patient,
                tooth=tooth,
                procedure_code=code,
                quadrant=quadrant
            )
            status_msg = generate_and_email_srp_pre_auth(treatment)
            print(status_msg)
            return redirect('pms_success')
        else:
            print("SRP Form Errors:", form.errors)  # 🔍 Add this line for debugging

    else:
        form = SRPTreatmentForm()

    return render(request, 'pms/submit_srp.html', {'form': form, 'patient': patient})

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

    # === Generate Crown Claim PDF Only View ===
@login_required
def generate_pdf(request, recommendation_id):
    recommendation = get_object_or_404(CrownRecommendation, id=recommendation_id)
    status_msg = generate_and_email_claim(recommendation)
    return render(request, 'claims/recommendation_success.html', {
        'email_status': status_msg
    })


