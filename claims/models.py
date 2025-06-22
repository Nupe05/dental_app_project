# Full Django Backend Script for Dental Crown Insurance Claim Automation

# STEP 1: Create models in claims/models.py
from django.db import models

class Patient(models.Model):
    name = models.CharField(max_length=100)
    dob = models.DateField()
    insurance_provider = models.CharField(max_length=100)
    policy_number = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ToothRecord(models.Model):
    TOOTH_CHOICES = [(i, f'Tooth {i}') for i in range(1, 33)]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    tooth_number = models.IntegerField(choices=TOOTH_CHOICES)
    xray_file = models.FileField(upload_to='xrays/')
    diagnosis = models.TextField()

    def __str__(self):
        return f"{self.patient.name} - Tooth {self.tooth_number}"


class CrownRecommendation(models.Model):
    CDT_CODE_CHOICES = [('D2740', 'Crown - porcelain/ceramic')]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    tooth = models.ForeignKey(ToothRecord, on_delete=models.CASCADE)
    cdt_code = models.CharField(max_length=10, choices=CDT_CODE_CHOICES, default='D2740')
    reason = models.TextField(blank=True)
    xray = models.FileField(upload_to='claims/', blank=True, null=True)
    clinical_note = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='Pending')  # Pending, Submitted, Denied, Approved
    submitted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Crown Claim: {self.patient.name} - Tooth {self.tooth.tooth_number}"

class TreatmentRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    tooth = models.ForeignKey(ToothRecord, on_delete=models.CASCADE)
    procedure_code = models.CharField(max_length=10)  # 'D2740' for crown
    created_at = models.DateTimeField(auto_now_add=True)
