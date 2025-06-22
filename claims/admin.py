from django.contrib import admin
from .models import Patient, ToothRecord, CrownRecommendation

admin.site.register(Patient)
admin.site.register(ToothRecord)
admin.site.register(CrownRecommendation)