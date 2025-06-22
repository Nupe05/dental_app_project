from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TreatmentRecord, CrownRecommendation
from .utils import generate_clinical_note
from .views import generate_and_email_claim

@receiver(post_save, sender=TreatmentRecord)
def auto_submit_claim(sender, instance, created, **kwargs):
    if created and instance.procedure_code == 'D2740':  # Crown
        tooth = instance.tooth
        patient = instance.patient

        rec = CrownRecommendation.objects.create(
            patient=patient,
            tooth=tooth,
            reason="Auto-generated via treatment record",
            xray=tooth.xray_file,
            clinical_note=generate_clinical_note(tooth.tooth_number, tooth.diagnosis),
            cdt_code='D2740'
        )

        generate_and_email_claim(rec)
