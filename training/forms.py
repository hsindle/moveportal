# training/forms.py
from django import forms
from django.forms.models import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div, HTML, Fieldset

# Local Model Imports
from .models import Course, Question, UserAttempt, OnboardingDocument # Ensure all are imported


class CourseForm(forms.ModelForm):
    """Primary form for creating/editing a training module."""
    class Meta:
        model = Course
        fields = ['title', 'video_url', 'required_for_groups', 'is_recurring']
        widgets = {
            'video_url': forms.URLInput(attrs={'placeholder': 'Paste YouTube or Vimeo video URL here...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Fieldset(
                'Course Settings',
                Row(
                    Column('title', css_class='col-md-6 mb-3'),
                    Column('video_url', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('required_for_groups', css_class='col-md-9 mb-3'),
                    Column('is_recurring', css_class='col-md-3 mb-3 d-flex align-items-center'),
                ),
                css_class='bg-white p-4 rounded-xl shadow-sm border-bottom border-primary mb-4'
            )
        )

# Form for individual quiz questions (used in the formset)
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        # Ensure 'correct_answer' is selected from the available options
        fields = ['text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
        }

# 🚨 Formset Factory: Allows multiple Question forms on one page 🚨
QuestionFormSet = inlineformset_factory(
    Course, 
    Question, 
    form=QuestionForm, 
    extra=1, 
    can_delete=True,
    min_num=1, # Ensure at least one question
    validate_min=True 
)

class OnboardingForm(forms.ModelForm):
    """Form for initial staff onboarding documentation."""
    
    # Custom fields needed for name, since AbstractUser fields are read-only in base forms
    # We will pass these to the view and update the user's name there.
    first_name = forms.CharField(label="First Name (Verify Accuracy)", required=True)
    last_name = forms.CharField(label="Last Name (Verify Accuracy)", required=True)
    
    class Meta:
        model = OnboardingDocument
        fields = [
            'first_name', 'last_name', # Custom fields for name confirmation
            'right_to_work_proof', 'p45_document', 
            'emergency_contact_name', 'emergency_contact_phone',
            'bank_name', 'account_holder_name', 'sort_code', 'account_number'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-8'
        
        # Crispy Layout
        self.helper.layout = Layout(
            HTML('<h4 class="pb-2 mb-3 border-bottom text-primary">Personal & Contact Details</h4>'),
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            Row(
                Column('emergency_contact_name', css_class='col-md-6'),
                Column('emergency_contact_phone', css_class='col-md-6'),
            ),
            
            HTML('<h4 class="pb-2 mb-3 border-bottom text-primary mt-4">Financial & Compliance</h4>'),
            Row(
                Column('bank_name', css_class='col-md-6'),
                Column('account_holder_name', css_class='col-md-6'),
            ),
            Row(
                Column('sort_code', css_class='col-md-6'),
                Column('account_number', css_class='col-md-6'),
            ),
            
            HTML('<h4 class="pb-2 mb-3 border-bottom text-primary mt-4">Required Documents</h4>'),
            'right_to_work_proof',
            'p45_document',
            
            Submit('submit', 'Submit & Lock Document', css_class='btn-success mt-4')
        )

