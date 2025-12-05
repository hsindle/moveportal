# checklists/forms.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

# 🚨 FIX: Imported IncidentLog and other models used in this file 🚨
from .models import ChecklistTemplate, ChecklistItem, IncidentLog, MaintenanceLog


class ChecklistTemplateForm(forms.ModelForm):
    class Meta:
        model = ChecklistTemplate
        fields = ['name', 'description', 'category', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        
        self.helper.layout = Layout(
            Field('name', css_class='mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-green-500 focus:ring-green-500'),
            Field('description', css_class='mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-green-500 focus:ring-green-500'),
            Field('category', css_class='mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-green-500 focus:ring-green-500'),
            Field('is_active'), # Checkbox field
        )


class ChecklistItemForm(forms.ModelForm):
    """Form for managers to create/edit individual checklist items."""
    class Meta:
        model = ChecklistItem
        fields = ['name', 'order', 'type']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('name', css_class='mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:ring-blue-500'),
            Field('order', css_class='mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:ring-blue-500'),
        )

class IncidentLogForm(forms.ModelForm):
    """Form used by Security/Managers to report an incident."""
    class Meta:
        model = IncidentLog
        fields = ['incident_type', 'location', 'persons_involved', 'summary', 'action_taken']

        widgets = {
            # 🚨 FIX 1: Add placeholder to summary and set rows 🚨
            'incident_type': forms.Textarea(attrs={'rows': 4, 'placeholder': 'e.g. Medical' }),

            'summary': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Please bullet point - ONLY write things you have seen yourself, dont be vague. If you didnt see it, dont write it.'}),
            
            # 🚨 FIX 2: Set rows for persons_involved to match summary 🚨
            'persons_involved': forms.Textarea(attrs={'rows': 4, 'placeholder': 'List names, physical descriptions, and relationship to the club (e.g., Guest, Staff).'}),
            
            'action_taken': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe immediate actions, security intervention, or police involvement.'}),
        }

class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        fields = ['location', 'description']
        labels = {
            'location': 'Location',
            'description': 'Description',
        }

