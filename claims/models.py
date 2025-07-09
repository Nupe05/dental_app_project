from django.db import models
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
import uuid
import random

class Patient(models.Model):
    name = models.CharField(max_length=100)
    dob = models.DateField()
    insurance_provider = models.CharField(max_length=100)
    policy_number = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class PatientXRay(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='xrays/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"X-ray for {self.patient.name} at {self.uploaded_at}"


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
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Submitted', 'Submitted'),
        ('Denied', 'Denied'),
        ('Approved', 'Approved'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    tooth = models.ForeignKey(ToothRecord, on_delete=models.CASCADE)
    cdt_code = models.CharField(max_length=10, choices=CDT_CODE_CHOICES, default='D2740')
    reason = models.TextField(blank=True)
    xray = models.FileField(upload_to='claims/', blank=True, null=True)
    clinical_note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    claim_id = models.CharField(max_length=20, blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)

    def mark_submitted(self):
        if not self.claim_id:
            self.claim_id = str(uuid.uuid4())[:8].upper()
        self.status = random.choices(
            ['Approved', 'Pending', 'Denied'],
            weights=[70, 20, 10],
            k=1
        )[0]
        self.submitted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Crown Claim: {self.patient.name} - Tooth {self.tooth.tooth_number}"


class TreatmentRecord(models.Model):
    QUADRANT_CHOICES = [
        ('UR', 'Upper Right'),
        ('UL', 'Upper Left'),
        ('LR', 'Lower Right'),
        ('LL', 'Lower Left'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Submitted', 'Submitted'),
        ('Denied', 'Denied'),
        ('Approved', 'Approved'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    tooth = models.ForeignKey(ToothRecord, on_delete=models.CASCADE, null=True, blank=True)
    procedure_code = models.CharField(max_length=10)  # D2740, D4341, D9944, etc.
    quadrant = models.CharField(max_length=2, choices=QUADRANT_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    claim_id = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(blank=True, null=True)

    def mark_submitted(self):
        if not self.claim_id:
            self.claim_id = str(uuid.uuid4())[:8].upper()
        self.status = random.choices(
            ['Approved', 'Pending', 'Denied'],
            weights=[70, 20, 10],
            k=1
        )[0]
        self.submitted_at = timezone.now()
        self.save()

        try:
            email = EmailMessage(
                subject=f"Treatment Submitted - {self.procedure_code}",
                body=f"Submitted treatment for {self.patient.name}, claim ID: {self.claim_id}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=["damon@dadswag.club"]
            )
            email.send()
        except Exception as e:
            print(f"[!] Email failed: {e}")

    def __str__(self):
        return f"{self.patient.name} - {self.procedure_code} - {self.status}"
