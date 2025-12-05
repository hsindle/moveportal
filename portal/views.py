# portal/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q, Count, Max, Prefetch, F
from django.contrib.auth.models import Group 

# Import Forms and Models
from accounts.forms import ManagerUserCreationForm, ManagerUserUpdateForm, StaffRegistrationForm
from accounts.models import CustomUser 
from training.models import UserAttempt, OnboardingDocument, Course


@login_required
def manager_dashboard(request):
    """
    Redirects unauthorized users, otherwise renders the dashboard.
    """
    # Unauthorized Check
    if request.user.groups.filter(name='Unauthorized').exists():
        return render(request, 'checklists/unauthorized_access.html')
        
    # Access Control Check
    if not request.user.groups.filter(name="Manager").exists():
        messages.error(request, "Access denied.")
        return redirect('checklists:home')

    # Forcefully consume and clear ALL queued messages
    list(messages.get_messages(request))

    # Render Dashboard
    return render(request, 'manager_dashboard.html', {})


@login_required
def manager_add_user(request):
    """Allows Managers to create a new user and assign a role."""
    
    if not request.user.groups.filter(name="Manager").exists():
        messages.error(request, "Access denied.")
        return redirect('manager_dashboard')

    if request.method == 'POST':
        form = ManagerUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{form.cleaned_data['username']}' created and assigned to the role.")
            return redirect('manager_dashboard')
    else:
        form = ManagerUserCreationForm()

    return render(request, 'manager_add_user.html', {'form': form})


@login_required
def manager_user_list(request):
    """
    Page to list ALL staff and management users for comprehensive oversight.
    Filters only users who have been assigned at least one role/group.
    """
    if not request.user.groups.filter(name="Manager").exists():
        messages.error(request, "Access denied.")
        return redirect('manager_dashboard')

    # Define ALL groups that should be visible (all operational/admin roles)
    all_roles = ['Manager', 'Supervisor', 'Bartender', 'Security', 'Unauthorized', 'Staff']
    
    # 1. Fetch all users who belong to ANY of the defined roles.
    staff_users_qs = CustomUser.objects.filter(
        groups__name__in=all_roles
    ).distinct().order_by('last_name', 'first_name')
    
    # --- 2. Final Context Calculation (Compliance Data) ---
    users_data = []
    
    # Pre-calculate the total count of required courses (used for compliance percentage)
    required_course_count = Course.objects.filter(
        required_for_groups__name__in=all_roles
    ).count()

    for user in staff_users_qs:
        
        # Determine Onboarding Status
        onboarding_status = 'N/A'
        is_security_exempt = user.groups.filter(name='Security').exists()

        if not is_security_exempt:
            try:
                doc = OnboardingDocument.objects.get(user=user)
                onboarding_status = 'Complete' if doc.is_completed else 'Pending'
            except OnboardingDocument.DoesNotExist:
                onboarding_status = 'Missing'
        else:
            onboarding_status = 'Exempt'

        # Determine Training Status
        total_passed = UserAttempt.objects.filter(user=user, is_passed=True).count()
        
        if required_course_count > 0:
            if total_passed >= required_course_count:
                 training_status = 'Complete'
            elif total_passed > 0:
                 training_status = f'Partial ({total_passed}/{required_course_count})'
            else:
                 training_status = 'Required'
        else:
            training_status = 'No Courses Defined' # Safety message if admin hasn't set up courses

        users_data.append({
            'user': user,
            'current_role': ', '.join(g.name for g in user.groups.all()),
            'onboarding_status': onboarding_status,
            'training_status': training_status,
            'account_status': 'Archived' if user.is_deleted else ('Active' if user.is_active else 'Inactive'),
        })
        
    return render(request, 'manager_user_list.html', {'staff_users': users_data})


@login_required
def manager_edit_user(request, user_id):
    """Page to edit a specific staff member's details and role, and view HR compliance."""
    if not request.user.groups.filter(name="Manager").exists():
        messages.error(request, "Access denied.")
        return redirect('manager_dashboard')

    user_to_edit = get_object_or_404(CustomUser, id=user_id)
    
    # 🚨 FIX 1: Fetch Onboarding Document 🚨
    try:
        onboarding_doc = OnboardingDocument.objects.get(user=user_to_edit)
    except OnboardingDocument.DoesNotExist:
        onboarding_doc = None
    
    if request.method == 'POST':
        # ... (POST processing remains here) ...
        form = ManagerUserUpdateForm(request.POST, instance=user_to_edit) 
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user_to_edit.username}'s details and role updated successfully.")
            return redirect('manager_user_list')
    else:
        form = ManagerUserUpdateForm(instance=user_to_edit) 
        
    context = {
        'form': form, 
        'user_to_edit': user_to_edit,
        'onboarding_doc': onboarding_doc, # 🚨 FIX 2: Pass the document to the template 🚨
    }
    return render(request, 'manager_edit_user.html', context)

def staff_register(request):
    """Handles public staff registration and role assignment."""
    
    if request.method == 'POST':
        # Initialize form, passing request for internal message handling
        form = StaffRegistrationForm(request.POST, request=request) 
        
        if form.is_valid():
            user = form.save() 

            messages.success(request, f"Account created for {user.username}. You may now log in.")
            return redirect('login') 
    else:
        # Initialize form for GET requests
        form = StaffRegistrationForm(request=request) 

    return render(request, 'registration/register.html', {'form': form})

@login_required
def manager_delete_user(request, user_id):
    """View to confirm and execute the soft deletion (archiving) of a staff user."""
    
    if not request.user.groups.filter(name="Manager").exists():
        messages.error(request, "Access denied.")
        return redirect('manager_dashboard')
    
    user_to_delete = get_object_or_404(CustomUser, id=user_id)
    
    # Safety Check: Prevent deleting the current manager
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own active account.")
        return redirect('manager_edit_user', user_id=user_id)
        
    if request.method == 'POST':
        user_name = user_to_delete.get_full_name()
        
        # 🚨 SOFT DELETE / ARCHIVE LOGIC 🚨
        user_to_delete.is_deleted = True # Set flag to hide user
        user_to_delete.is_active = False # Deactivate login access
        user_to_delete.groups.clear()     # Remove all role groups
        
        # Optional: Render the username unusable by appending a timestamp
        # user_to_delete.username = f"{user_to_delete.username}_{timezone.now().timestamp()}" 
        # user_to_delete.email = f"{user_to_delete.id}.DELETED" 
        
        user_to_delete.save()
        
        messages.success(request, f"User '{user_name}' has been successfully ARCHIVED. All historical records remain.")
        return redirect('manager_user_list')
        
    # Render Confirmation Page (GET request)
    return render(request, 'manager_user_confirm_delete.html', {
        'user_to_delete': user_to_delete
    })