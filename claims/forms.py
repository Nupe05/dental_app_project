from django import forms
from .models import CrownRecommendation, ToothRecord, TreatmentRecord

class CrownRecommendationForm(forms.ModelForm):
    class Meta:
        model = CrownRecommendation
        fields = ['patient', 'tooth', 'cdt_code', 'reason', 'xray', 'clinical_note']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
            'clinical_note': forms.Textarea(attrs={'rows': 4}),
        }

class SRPTreatmentForm(forms.Form):
    procedure_code = forms.ChoiceField(
        choices=[('D4341', 'SRP - Four or more teeth per quadrant')],
        initial='D4341',
        label='CDT Code'
    )
    tooth_number = forms.ChoiceField(
        choices=[(str(i), f"Tooth {i}") for i in range(1, 33)],
        label='Tooth Number'
    )
    quadrant = forms.ChoiceField(
        choices=[
            ('UR', 'Upper Right'),
            ('UL', 'Upper Left'),
            ('LR', 'Lower Right'),
            ('LL', 'Lower Left'),
        ],
        label='Quadrant'
    )

class OcclusalGuardForm(forms.Form):
    procedure_code = forms.CharField(
        initial='D9944',  # CDT for occlusal guard
        widget=forms.HiddenInput()
    )
