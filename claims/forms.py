from django import forms
from .models import CrownRecommendation

class CrownRecommendationForm(forms.ModelForm):
    class Meta:
        model = CrownRecommendation
        fields = ['patient', 'tooth', 'reason']


