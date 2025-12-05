# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.urls import reverse_lazy
from .forms import ManagerUserCreationForm, ManagerUserUpdateForm
from .models import CustomUser
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# ----- Authentication Views -----

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:profile')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('accounts:profile')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('accounts:login')

def profile_view(request):
    return render(request, 'accounts/profile.html')


# ----- Password Change Views -----

@login_required
def manager_edit_user(request, user_id):
    if not request.user.groups.filter(name='Manager').exists():
        messages.error(request, "Access denied.")
        return redirect('manager_dashboard')

    user_to_edit = get_object_or_404(CustomUser, id=user_id)
    form = ManagerUserUpdateForm(request.POST or None, instance=user_to_edit)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"{user_to_edit.username} updated successfully.")
        return redirect('manager_dashboard')

    return render(request, 'manager/edit_user.html', {'form': form, 'user_to_edit': user_to_edit})
