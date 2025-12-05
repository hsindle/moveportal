# checklists/reporting_views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from datetime import date, time, timedelta
from operator import attrgetter
from itertools import groupby 
from .views import get_operational_date, check_manager_access # Import core helpers

# CRITICAL: Import models and forms locally within the functions if necessary, 
# or ensure they are imported cleanly here if no circular path exists.

from .models import ChecklistTemplate, ChecklistSession, ItemResponse, IncidentLog


# checklists/reporting_views.py (Focus on log_incident function)

# checklists/reporting_views.py (Focus on log_incident function)

@login_required
def log_incident(request):
    """
    Form for Manager/Security to log an incident. The saved log is immediately locked.
    """
    from .forms import IncidentLogForm # Local import
    from .models import IncidentLog # Local Model Import (Used in exception/error checks)
    
    user_groups = request.user.groups.values_list('name', flat=True)
    if 'Manager' not in user_groups and 'Security' not in user_groups:
        messages.error(request, "You do not have permission to log incidents.")
        return redirect('checklists:daily_view_content') 
    
    if request.method == 'POST':
        form = IncidentLogForm(request.POST)
        if form.is_valid():
            # 🚨 FIX: COMPLETE SAVING LOGIC HERE 🚨
            incident = form.save(commit=False)
            
            # Set system fields
            incident.reported_by = request.user
            incident.operational_date = get_operational_date()
            incident.is_locked = True 
            
            incident.save() # <-- CRITICAL: Now 'incident' is saved and has an ID
            
            messages.success(request, f"Incident Log #{incident.id} recorded successfully and is now locked.")
            return redirect('checklists:daily_view_content') 
        else:
            # If form is invalid, just let execution continue to render the form with errors
            pass 
    else:
        form = IncidentLogForm()

    return render(request, 'checklists/incident_log_form.html', {'form': form,})

# ... (The rest of reporting_views.py follows) ...


@login_required
def incident_history(request):
    """
    Shows a list of all incidents, filtered by date range and type.
    """
    if not check_manager_access(request):
        if not request.user.groups.filter(name="Supervisor").exists():
            return redirect('manager_dashboard')
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    incident_type = request.GET.get('incident_type')

    incidents = IncidentLog.objects.all().order_by('-timestamp')

    if start_date: incidents = incidents.filter(operational_date__gte=start_date)
    if end_date: incidents = incidents.filter(operational_date__lte=end_date)
    if incident_type: incidents = incidents.filter(incident_type__icontains=incident_type)
        
    incidents_data = list(incidents.select_related('reported_by'))
    incidents_data.sort(key=lambda x: x.operational_date, reverse=True)
    
    grouped_incidents = []
    for date_key, group in groupby(incidents_data, key=lambda x: x.operational_date):
        grouped_incidents.append({'date': date_key, 'incidents': list(group)})
        
    all_incident_types = IncidentLog.objects.values_list('incident_type', flat=True).distinct().order_by('incident_type')


    return render(request, 'checklists/incident_history.html', {
        'grouped_incidents': grouped_incidents,
        'incident_types': all_incident_types,
        'selected_incident_type': incident_type,
        'start_date': start_date,
        'end_date': end_date,
    })



@login_required
def session_completion_detail(request, session_id):
    """
    Shows detailed per-item completion for a given checklist session.
    """
    if not check_manager_access(request):
        if not request.user.groups.filter(name="Supervisor").exists():
            return redirect('manager_dashboard')

    session = get_object_or_404(ChecklistSession, pk=session_id)

    responses = (
        ItemResponse.objects
        .filter(session=session)
        .select_related('item', 'performed_by')
        .order_by('item__order')
    )

    return render(request, "checklists/session_completion_detail.html", {
        "session": session,
        "responses": responses,
    })

@login_required
def session_history(request, session_id):
    # Get the session
    session = get_object_or_404(ChecklistSession, id=session_id)

    # Get all item responses for this session
    item_responses = session.itemresponse_set.all()

    context = {
        'session': session,
        'item_responses': item_responses,
    }
    return render(request, 'checklists/session_history.html', context)

# checklists/reporting_views.py (inside maintenance_log_create)

@login_required
def maintenance_log_create(request):
    """Create a new maintenance log (Modeled after Incident Log)."""
    from .forms import MaintenanceLogForm
    from .models import MaintenanceLog # Ensure model is imported locally

    # 🚨 REMOVED ACCESS CHECK 🚨
    # The view is already protected by @login_required, so any authenticated staff can log maintenance.
    
    if request.method == 'POST':
        form = MaintenanceLogForm(request.POST)
        if form.is_valid():
            maintenance_log = form.save(commit=False)
            
            # Set system fields
            maintenance_log.reported_by = request.user
            maintenance_log.timestamp = timezone.now()
            maintenance_log.operational_date = get_operational_date()
            maintenance_log.is_locked = True 
            
            maintenance_log.save()
            
            messages.success(request, f"Maintenance Log '{maintenance_log.title}' recorded and locked.")
            return redirect('checklists:maintenance_history')
    else:
        form = MaintenanceLogForm()

    return render(request, 'checklists/maintenance_log_form.html', {'form': form})


@login_required
def maintenance_history(request):
    """List all maintenance logs grouped by operational date, with filtering."""
    from .models import MaintenanceLog # Ensure model is imported locally

    if not check_manager_access(request) and not request.user.groups.filter(name="Supervisor").exists():
        messages.error(request, "Access denied.")
        return redirect('manager_dashboard')
        
    # Get logs and filtering logic
    logs = MaintenanceLog.objects.all().order_by('-operational_date', '-timestamp')
    
    # ... (Add GET filtering logic similar to incident_history here) ...
    
    # Group by operational_date
    grouped_logs = []
    for date, group in groupby(logs, key=attrgetter('operational_date')):
        grouped_logs.append({'date': date, 'logs': list(group)})

    context = {
        'grouped_logs': grouped_logs,
        # ... (Add filter context if needed) ...
    }
    return render(request, 'checklists/maintenance_history.html', context)

@login_required
def checklist_history(request):
    """
    Shows all checklist sessions grouped by day, with completion status.
    Read-only access for managers/supervisors.
    """
    if not check_manager_access(request) and not request.user.groups.filter(name="Supervisor").exists():
        return redirect('manager_dashboard')
    
    # Filtering
    template_id = request.GET.get('template')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    sessions = ChecklistSession.objects.all().order_by('-date')
    if template_id: sessions = sessions.filter(template_id=template_id)
    if start_date: sessions = sessions.filter(date__gte=start_date)
    if end_date: sessions = sessions.filter(date__lte=end_date)
    
    # Compute completion per session
    sessions_data = []

    for session in sessions:

        # ✅ Only real checklist items (ignore headings)
        total_items = session.template.items.filter(type="item").count()

        # ✅ Only done real items
        done_responses = ItemResponse.objects.filter(
            session=session,
            item__type="item",
            status="done"
        ).count()

        # ✅ Completion logic now matches your live checklist screen
        is_completed = (total_items > 0 and done_responses == total_items)

        # ✅ Completion time = last real item completed
        latest_done = ItemResponse.objects.filter(
            session=session,
            item__type="item",
            status="done"
        ).order_by('-performed_at').first()

        completion_time = latest_done.performed_at if latest_done else None

        sessions_data.append({
            'session': session,
            'is_completed': is_completed,
            'completion_time': completion_time,
        })
    
    # Group sessions by date for the template
    grouped_sessions = []
    sessions_data.sort(key=lambda x: x['session'].date, reverse=True)
    for date_key, group in groupby(sessions_data, key=lambda x: x['session'].date):
        grouped_sessions.append({'date': date_key, 'sessions': list(group)})

    all_templates = ChecklistTemplate.objects.all().order_by('name')

    return render(request, 'checklists/history_dashboard.html', {
        'grouped_sessions': grouped_sessions,
        'all_templates': all_templates,
        'selected_template_id': template_id,
        'start_date': start_date,
        'end_date': end_date,
    })


