# rota/forms.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from .models import Shift
from accounts.models import CustomUser 
from django.contrib.auth.models import Group
from datetime import time, timedelta, datetime

# --- HELPER FUNCTION: Generate 15-minute time choices ---
def get_time_choices(interval_minutes=15):
    """Generates a list of time choices (e.g., '00:00', '00:15', ..., '23:45')."""
    choices = []
    start = datetime.strptime("00:00", "%H:%M")
    end = datetime.strptime("23:59", "%H:%M")
    
    current = start
    while current <= end:
        time_str = current.strftime("%H:%M")
        choices.append((time_str, time_str))
        current += timedelta(minutes=interval_minutes)
        
    return choices

# Define the standard 15-minute choices once
TIME_CHOICES = get_time_choices(15)

class ShiftForm(forms.ModelForm):
    """Form for Managers to create and edit shifts."""
    
    schedulable_roles = ['Bartender', 'Security', 'Staff', 'Manager', 'Supervisor']

    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(groups__name__in=schedulable_roles).distinct().order_by('first_name'),
        label="Staff Member"
    )

    operational_date = forms.DateField(widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))

    # 🚨 FIX 1: Replace TimeField with ChoiceField for 15-min intervals 🚨
    start_time = forms.ChoiceField(choices=TIME_CHOICES, required=True)
    
    # 🚨 FIX 2: Add 'CLOSE' option to end time choices 🚨
    END_TIME_CHOICES = [('CLOSE', 'CLOSE')] + TIME_CHOICES
    end_time = forms.ChoiceField(choices=END_TIME_CHOICES, required=True)


    class Meta:
        model = Shift
        fields = ['user', 'operational_date', 'start_time', 'end_time', 'notes'] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Field('user', css_class='form-control'),
            Field('operational_date', css_class='form-control'),
            
            # Use columns for time fields if possible
            Field('start_time', css_class='form-control'),
            Field('end_time', css_class='form-control'),
            
            Field('notes', css_class='form-control', rows='3'),
            
            Submit('submit', 'Save Shift', css_class='btn-success mt-4')
        )
        
    # 🚨 FIX 3: Clean method to handle 'CLOSE' submission 🚨
    def clean_end_time(self):
        end_time_value = self.cleaned_data.get('end_time')
        
        if end_time_value == 'CLOSE':
            # This is a flag for the database. We return None, but the model needs to allow nulls.
            return None 
            
        # If it's a standard time, it gets returned as a string ('HH:MM')
        return end_time_value

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        # NOTE: Since the fields are ChoiceFields, they return strings ('HH:MM'), not time objects.
        
        # If both are valid times (not None) and not 'CLOSE', ensure start is before end
        if start and end and end != 'CLOSE':
            
            # Convert strings to datetime objects for comparison
            start_dt = datetime.strptime(start, "%H:%M")
            end_dt = datetime.strptime(end, "%H:%M")
            
            # If the shift crosses midnight (e.g., 22:00 to 03:00), the end time must be earlier
            # If start is later than end, assume it crosses midnight and is valid
            if start_dt > end_dt:
                pass # Crosses midnight, assumed valid (e.g., 22:00 to 03:00)
            elif start_dt == end_dt:
                 raise forms.ValidationError("Start time and end time cannot be the same.")
            elif start_dt < end_dt:
                pass # Standard shift, valid (e.g., 10:00 to 18:00)
                
        # We allow start time to be set even if end time is CLOSE (or None after cleaning)
        
        return cleaned_data