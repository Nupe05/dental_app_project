from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, JsonResponse
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
from .utils import generate_and_email_claim, generate_and_email_srp_pre_auth

# === Centralized CDT Codes ===
CDT_CODES = {
    'CROWN': 'D2740',
    'SRP': 'D4341',
}

# === PMS Home View ===
@login_required
def pms_home(request):
    patients = Patient.objects.all()
    return render(request, 'pms/home.html', {'patients': patients})

# === Patient Detail View ===
@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    teeth = ToothRecord.objects.filter(patient=patient)
    return render(request, 'pms/patient_detail.html', {'patient': patient, 'teeth': teeth})

# === Add Crown Treatment View ===
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

# === Submit SRP Treatment View ===
@login_required
def submit_srp_treatment(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == 'POST':
        code = request.POST.get('procedure_code', CDT_CODES['SRP'])
        tooth_number = request.POST.get('tooth_number', '1')
        tooth = ToothRecord.objects.filter(patient=patient, tooth_number=tooth_number).first()

        if not tooth:
            return JsonResponse({"error": "Tooth record not found."}, status=400)

        treatment = TreatmentRecord.objects.create(
            patient=patient,
            tooth=tooth,
            procedure_code=code
        )
        status_msg = generate_and_email_srp_pre_auth(treatment)
        print(status_msg)
        return redirect('pms_success')

    return render(request, 'pms/submit_srp.html', {'patient': patient})

# === PMS Success Page ===
def pms_success(request):
    return render(request, 'pms/success.html')

# === Create Crown Recommendation View ===
def create_crown_recommendation(request):
    if request.method == 'POST':
        form = CrownRecommendationForm(request.POST)
        if form.is_valid():
            recommendation = form.save()
            return redirect('generate_pdf', recommendation_id=recommendation.id)
    else:
        form = CrownRecommendationForm()
    return render(request, 'claims/recommendation_form.html', {'form': form})

# === Generate PDF and Send Email View ===
def generate_pdf(request, recommendation_id):
    recommendation = get_object_or_404(CrownRecommendation, id=recommendation_id)
    email_status = generate_and_email_claim(recommendation)
    return render(request, 'claims/recommendation_success.html', {
        'email_status': email_status
    })

# === Recommendation Success Page ===
def recommendation_success(request):
    return render(request, 'claims/recommendation_success.html')

# === API: Create TreatmentRecord View ===
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

        # HL7 format
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