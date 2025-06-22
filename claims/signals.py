from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CrownRecommendation
from .utils import generate_clinical_note

@receiver(post_save, sender=CrownRecommendation)
def populate_crown_claim(sender, instance, created, **kwargs):
    if created and not instance.clinical_note:
        instance.xray = instance.tooth.xray_file
        instance.clinical_note = generate_clinical_note(instance.tooth.tooth_number, instance.tooth.diagnosis)
        instance.save()