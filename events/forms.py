# events/forms.py
from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Button, Row, Column, Field, Div, HTML, Fieldset
from crispy_forms.bootstrap import StrictButton
from django.contrib import messages

from .models import Event, EventArtwork, EventCategory, Promoter 
from accounts.models import CustomUser 
from django.contrib.auth.models import Group


# --- Helper Functions ---
def get_schedulable_users():
    schedulable_roles = ['Bartender', 'Security', 'Staff', 'Manager', 'Supervisor']
    return CustomUser.objects.filter(groups__name__in=schedulable_roles).distinct().order_by('first_name')

# --- Event Form ---
class EventForm(forms.ModelForm):
    
    # --- Custom Category Fields ---
    new_category_name = forms.CharField(max_length=50, required=False, label="OR Add New Category Name")
    new_category_color = forms.CharField(max_length=7, required=False, label="Color Code (e.g., #007bff)")
    
    # --- Custom Promoter Fields ---
    new_promoter_name = forms.CharField(max_length=100, required=False, label="OR Add New Promoter Name")
    new_promoter_email = forms.EmailField(max_length=100, required=False, label="New Promoter Email")
    new_promoter_phone = forms.CharField(max_length=20, required=False, label="New Promoter Phone")
    
    # Overriding Foreign Key fields to allow selection of existing objects
    category = forms.ModelChoiceField(
        queryset=EventCategory.objects.all().order_by('name'), required=False, label="Select Event Category",
    )
    promoter = forms.ModelChoiceField(
        queryset=Promoter.objects.filter(is_active=True).order_by('name'),
        required=False,
        label="Select Existing Promoter",
    )
    
    # Overriding the team field (M2M)
    team = forms.ModelMultipleChoiceField(
        queryset=get_schedulable_users(), required=False, label="Staff Assigned",
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Event
        fields = [
            "name", "start_date", "end_date", "is_active", 
            "category", "promoter", "team", 
            "epk_link", "hospitality_rider", "technical_rider", 
            "notes"
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        new_cat_name = cleaned_data.get('new_category_name')
        new_cat_color = cleaned_data.get('new_category_color')
        
        # Validation Check 1: Category Creation Consistency
        if new_cat_name and not new_cat_color:
            raise ValidationError({'new_category_color': ["If you provide a New Category Name, you must provide a Color Code."]})
        
        # Validation Check 2: Promoter Name Uniqueness (for new promoter)
        new_promoter_name = cleaned_data.get('new_promoter_name')
        if new_promoter_name and Promoter.objects.filter(name=new_promoter_name).exists():
            raise ValidationError({'new_promoter_name': [f"A promoter named '{new_promoter_name}' already exists."]})
            
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensure all fields except 'name' are explicitly NOT required
        for field_name in self.fields:
            if field_name != 'name':
                self.fields[field_name].required = False
        
        # Remove Crispy helper setup here as we are manually rendering the layout
        
    @transaction.atomic
    def save(self, commit=True, *args, **kwargs):
        
        # 1. Resolve Dynamic Category
        new_cat_name = self.cleaned_data.get('new_category_name')
        if new_cat_name:
            category, _ = EventCategory.objects.get_or_create(
                name=new_cat_name,
                defaults={'color_code': self.cleaned_data.get('new_category_color', '#cccccc')}
            )
            self.instance.category = category
        elif not self.cleaned_data.get('category'):
            # 🚨 FIX 1: Explicitly set FK to None if neither select nor new field is filled 🚨
            self.instance.category = None 
        
        # 2. Resolve Dynamic Promoter
        new_promoter_name = self.cleaned_data.get('new_promoter_name')
        if new_promoter_name:
            promoter, _ = Promoter.objects.get_or_create(
                name=new_promoter_name,
                defaults={
                    'email': self.cleaned_data.get('new_promoter_email'),
                    'phone': self.cleaned_data.get('new_promoter_phone')
                }
            )
            self.instance.promoter = promoter
        elif not self.cleaned_data.get('promoter'):
            # 🚨 FIX 2: Explicitly set FK to None if neither select nor new field is filled 🚨
            self.instance.promoter = None
        
        # 3. Handle M2M save separately
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            self.save_m2m() # Saves the 'team' M2M field
        
        return instance


class EventArtworkForm(forms.ModelForm):
    """Form for managers to upload artwork files related to an event."""
    class Meta:
        model = EventArtwork
        fields = ['title', 'image']

class PromoterForm(forms.ModelForm):
    class Meta:
        model = Promoter
        fields = ['name', 'email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
class EventCategoryForm(forms.ModelForm):
    class Meta:
        model = EventCategory
        fields = ['name', 'color_code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            # Use color input widget for easier color selection
            'color_code': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}), 
        }