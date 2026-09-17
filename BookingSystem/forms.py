from django import forms
from .models import Booking
from django.contrib.auth.forms import AuthenticationForm

class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control w-100',
            'placeholder': 'Username',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control w-100',
            'placeholder': 'Password',
        })

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['title', 'conference_date', 'start_time', 'end_time', 'additional_support']
        widgets = {
            'conference_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'additional_support': forms.Textarea(attrs={'rows': 3}),
        }
