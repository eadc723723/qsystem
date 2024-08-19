from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Counter, Activity, CounterActivityAssignment

class UsernameAuthenticationForm(forms.Form):
    username = forms.ModelChoiceField(
        queryset=User.objects.exclude(is_superuser=True),  # Exclude superusers if needed
        label='Select User',
        widget=forms.Select(attrs={'class': 'select is-primary'})  # Apply Bulma's select class
    )

class StaffSignInForm(forms.Form):
    counter = forms.ModelChoiceField(queryset=Counter.objects.filter(status='offline'), label='Select Counter')
    activity = forms.ModelChoiceField(queryset=Activity.objects.filter(mode='active'), label='Select Activity')

    def clean(self):
        cleaned_data = super().clean()
        counter = cleaned_data.get('counter')
        activity = cleaned_data.get('activity')

        # Check if the counter is already assigned to the activity for today
        if CounterActivityAssignment.objects.filter(counter=counter, activity=activity, date=timezone.now().date()).exists():
            raise forms.ValidationError('This counter is already assigned to this activity today.')

        return cleaned_data
