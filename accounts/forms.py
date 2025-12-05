# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.db import transaction
from django.contrib import messages

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field 

# Assuming your CustomUser model is imported here or in another file accessible to forms.py
from .models import CustomUser 
# Assuming you have defined the custom layout in accounts/layout.py
from .layout import MANAGER_ADD_USER_LAYOUT 


class ManagerUserCreationForm(UserCreationForm):
    """
    Form for creating a new user. Now shows ALL groups so Managers can select
    Security, Bartender, Manager, or Supervisor.
    """
    # 🚨 FIX: Removed the exclusion filter 🚨
    # This allows a Manager to create other Manager/Supervisor users.
    roles = forms.ModelChoiceField(
        queryset=Group.objects.all().order_by('name'),
        required=True,
        label="Staff Role"
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'roles')

    def save(self, commit=True):
        # 1. Create the user object
        user = super().save(commit=False)
        user.is_active = True

        if commit:
            user.save()
            # 2. Assign the selected role (Group)
            self.cleaned_data['roles'].user_set.add(user)
        
        return user


class ManagerUserUpdateForm(UserChangeForm):
    """
    Form for Managers to update existing user details and change their staff role.
    """
    # 🚨 FIX: This field now shows ALL groups for full flexibility 🚨
    roles = forms.ModelChoiceField(
        queryset=Group.objects.all().order_by('name'),
        required=False,
        label="Staff Role"
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'roles', 'is_active')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pre-select the current role based on ALL groups
        if self.instance.groups.exists():
            current_group = self.instance.groups.first()
            self.initial['roles'] = current_group

        # Initialize Crispy FormHelper and layout
        from crispy_forms.helper import FormHelper
        self.helper = FormHelper()
        self.helper.layout = MANAGER_ADD_USER_LAYOUT 
        self.fields.pop('password', None)
        
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # 2. Update Role (Groups)
        new_role = self.cleaned_data.get('roles')
        
        # Only process if a role was actually selected/changed
        if new_role:
            # Clear ALL current groups attached to the user
            user.groups.clear()
            
            # Assign the new selected role
            user.groups.add(new_role)

        if commit:
            user.save()
        return user
    
class StaffRegistrationForm(UserCreationForm):
    """
    Public registration form for new staff members.
    1. Sets username = first_name + last_name.
    2. Defaults role to the "Unauthorized" group.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('first_name', 'last_name', 'email')
        
    def clean(self):
            cleaned_data = super().clean()
            first_name = cleaned_data.get('first_name')
            last_name = cleaned_data.get('last_name')
            
            # Enforce First and Last Name
            if not first_name or not last_name:
                raise ValidationError("You must provide both your First Name and Last Name.")

            # 🚨 FIX: Set the username as the combined full name without a separator 🚨
            full_name_username = f"{first_name} {last_name}".lower()
            
            # Change from .replace(' ', '.') to .replace(' ', '')
            cleaned_data['username'] = full_name_username.replace(' ', '') 

            # Ensure the generated username is unique
            if CustomUser.objects.filter(username=cleaned_data['username']).exists():
                raise ValidationError("A user with this full name already exists. Please contact a manager.")
                
            return cleaned_data
    
    def __init__(self, *args, **kwargs):
        # 🚨 FIX 1: Pop the request object and store it 🚨
        self.request = kwargs.pop('request', None) 
        super().__init__(*args, **kwargs)

    @transaction.atomic
    def save(self, commit=True, request=None):
        user = super().save(commit=False)
        user.is_active = False # Account is inactive until authorized
        
        # 🚨 FIX: Explicitly set the username from cleaned_data 🚨
        # This prevents the username field from being Null/empty on save.
        user.username = self.cleaned_data.get('username') 
        
        if commit:
            user.save()
            
            try:
                unauth_group = Group.objects.get(name='Unauthorized')
            except Group.DoesNotExist:
                # Check if request is available before adding message
                if request:
                    messages.error(request, "CRITICAL: 'Unauthorized' group not found. Contact Manager.")
                return user
            
            user.groups.add(unauth_group)
        
        return user