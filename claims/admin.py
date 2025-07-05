from django.contrib import admin
from .models import Patient, ToothRecord, CrownRecommendation
from .models import PatientXRay

admin.site.register(PatientXRay)
admin.site.register(Patient)
admin.site.register(ToothRecord)
admin.site.register(CrownRecommendation)
