# rota/views.py
from datetime import date, timedelta, datetime, time
from itertools import groupby
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import CustomUser
from .forms import ShiftForm
from .models import Shift
from django.contrib.auth.models import Group 
from django.urls import reverse


# --- Helper Functions ---
def is_manager_or_supervisor(user):
    """Return True if user belongs to Manager or Supervisor groups."""
    return user.groups.filter(name__in=["Manager", "Supervisor"]).exists()

def get_user_sort_key(user, hierarchy_list):
    """Returns a tuple for sorting users by highest priority group."""
    user_groups = user.groups.values_list('name', flat=True)
    priority = len(hierarchy_list) 
    
    for group_name in user_groups:
        try:
            rank = hierarchy_list.index(group_name)
            priority = min(priority, rank)
        except ValueError:
            continue
            
    # Stable sort by (Priority, Last Name, First Name)
    return (priority, user.last_name, user.first_name)


# --- ROTA VIEWER (Now renders the complete, sorted grid) ---
@login_required
def rota_view(request):
    """
    Displays the user's personal shifts and the full team rota stacked vertically.
    This view runs the full shift_admin fetching/sorting logic.
    """
    is_manager_access = is_manager_or_supervisor(request.user)
    
    # 1. Determine the current week start and end
    today = date.today()
    week_offset = int(request.GET.get('offset', 0))
    week_start_date = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_end_date = week_start_date + timedelta(days=6)
    
    date_range = [week_start_date + timedelta(days=i) for i in range(7)]

    # 2. Fetch ALL shifts for the current week
    shifts_qs = Shift.objects.filter(
        operational_date__gte=week_start_date,
        operational_date__lte=week_end_date
    ).select_related('user').order_by('user__first_name', 'operational_date', 'start_time')
    
    shifts_list = list(shifts_qs)
    
    # --- 3. Separate Data: Personal and Team Rota ---
    
    # Personal Shifts: Filtered for current user
    personal_shifts = [
        shift for shift in shifts_list if shift.user == request.user
    ]
    
    # Team Rota: Group ALL shifts by user's full name
    team_rota = {}
    shifts_list.sort(key=lambda x: x.user.get_full_name())
    
    for full_name, group in groupby(shifts_list, key=lambda x: x.user.get_full_name()):
        team_rota[full_name] = list(group)
    
    context = {
        'is_manager_access': is_manager_access,
        'personal_shifts': personal_shifts, 
        'team_rota': team_rota,             
        'date_range': date_range,
        'week_start': week_start_date,
        'week_end': week_end_date,
        'current_offset': week_offset,
    }

    return render(request, 'rota/rota_viewer.html', context)


# --- ROTA ADMIN GRID (For Manager use only) ---
@login_required
def shift_admin(request):
    """Lists all users and shifts in a weekly grid, sorted by hierarchy."""
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('checklists:home')

    today = date.today()
    week_offset = int(request.GET.get('offset', 0))
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_end = week_start + timedelta(days=6)
    date_range = [week_start + timedelta(days=i) for i in range(7)]

    # 1. Define Hierarchy Order
    HIERARCHY = ['Manager', 'Supervisor', 'Bartender', 'Security', 'Unauthorized']
    
    # 2. Fetch ALL relevant users and prefetch groups for Python sorting
    users_qs = CustomUser.objects.filter(
        Q(groups__name__in=HIERARCHY) | Q(is_superuser=True) # Ensure superusers are included
    ).distinct().prefetch_related('groups').order_by('last_name', 'first_name')
    
    # 3. Sort Users by Hierarchy (in Python)
    users_sorted = sorted(users_qs, key=lambda u: get_user_sort_key(u, HIERARCHY))
    
    # 4. Fetch shifts for the week
    shifts = Shift.objects.filter(
        operational_date__range=(week_start, week_end)
    ).select_related('user')

    shift_map = {(s.user_id, s.operational_date): s for s in shifts}

    # 5. Build rota grid
    rota_grid = []
    for user in users_sorted:
        user_row = {'user': user, 'shifts': {}} 
        
        for d in date_range:
            shift = shift_map.get((user.id, d))
            
            if shift:
                start_str = shift.start_time.strftime('%H:%M') if shift.start_time else ''
                end_str = shift.end_time.strftime('%H:%M') if shift.end_time else 'CLOSE'
                position_display = f" ({shift.position})" if shift.position else ""
                display = f"{start_str} - {end_str}{position_display}"

                user_row['shifts'][d] = {'type': 'shift', 'id': shift.id, 'display': display}
            else:
                user_row['shifts'][d] = {'type': 'empty', 'date': d}
        rota_grid.append(user_row)

    context = {
        'date_range': date_range,
        'rota_grid': rota_grid,
        'week_start': week_start,
        'week_end': week_end,
        'current_offset': week_offset
    }
    return render(request, 'rota/shift_admin.html', context)


# --- SHIFT EDIT / ADD ---
@login_required
def shift_edit(request, shift_id=None):
    """Handles creating or editing a shift."""
    from .forms import ShiftForm
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('checklists:home')

    # Fix for shift_id=0 passed by the grid link (handled as new shift)
    if shift_id is None or shift_id == 0:
        instance = None
    else:
        instance = get_object_or_404(Shift, pk=shift_id)

    initial_data = {}
    if instance is None:
        initial_data['user'] = request.GET.get('user_id')
        initial_data['operational_date'] = request.GET.get('date')
        
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Shift saved successfully.")
            return redirect('rota:shift_admin')
    else:
        form = ShiftForm(instance=instance, initial=initial_data)

    page_title = "Schedule New Shift"
    if instance:
        page_title = f"Edit Shift for {instance.user.get_full_name()}"
        
    context = {
        'form': form,
        'is_new': instance is None,
        'shift_id': shift_id,
        'page_title': page_title,
    }
    return render(request, 'rota/shift_form.html', context)


# --- SHIFT DELETE ---
@login_required
def shift_delete(request, shift_id):
    """Deletes a shift after confirmation."""
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('checklists:home')

    shift = get_object_or_404(Shift, pk=shift_id)

    if request.method == 'POST':
        shift.delete()
        messages.success(request, f"Shift for {shift.user.get_full_name()} on {shift.operational_date} deleted.")
        return redirect('rota:shift_admin')

    return render(request, 'rota/shift_confirm_delete.html', {'shift': shift})