from django.contrib.auth.models import User
from django import forms

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ["username", "email", "password"]


SCORE_HELP = "0–100"
class CareerInputForm(forms.Form):
    math = forms.FloatField(min_value=0, max_value=100, help_text=SCORE_HELP)
    science = forms.FloatField(min_value=0, max_value=100, help_text=SCORE_HELP)
    english = forms.FloatField(min_value=0, max_value=100, help_text=SCORE_HELP)
    arts = forms.FloatField(label="Arts/Design", min_value=0, max_value=100, help_text=SCORE_HELP)

    coding = forms.FloatField(min_value=0, max_value=100, help_text=SCORE_HELP)
    design = forms.FloatField(min_value=0, max_value=100, help_text=SCORE_HELP)
    leadership = forms.FloatField(min_value=0, max_value=100, help_text=SCORE_HELP)
    communication = forms.FloatField(min_value=0, max_value=100, help_text=SCORE_HELP)

    interests = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=False)
