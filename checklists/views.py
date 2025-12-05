# checklists/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from datetime import time, timedelta
from itertools import groupby 

# Import models necessary for core view functions
from .models import ChecklistTemplate, ChecklistSession, ItemResponse, ChecklistItem


# --- HELPER FUNCTION: Calculates the Operational Date ---
def get_operational_date():
    """
    Determines the correct operational date based on a 5:00 AM (05:00) cutoff.
    """
    now = timezone.localtime(timezone.now())
    cutoff_time = time(5, 0, 0)

    if now.time() < cutoff_time:
        operational_date = now.date() - timedelta(days=1)
    else:
        operational_date = now.date()
        
    return operational_date


# --- Helper for checking Manager permission ---
def check_manager_access(request):
    """Checks if the current user is a Manager."""
    if not request.user.groups.filter(name="Manager").exists():
        messages.error(request, "Access denied. Only Managers can manage templates.")
        return False
    return True


def is_manager_or_supervisor(user):
    """Return True if user is Manager or Supervisor."""
    return user.groups.filter(name__in=["Manager", "Supervisor"]).exists()


# checklists/views.py

@login_required
def home(request):
    """
    Primary landing page. Renders the Operational Hub (Tiles) for ALL users.
    Managers must click the Dashboard tile to access admin features.
    """
    # 🚨 FIX: Removed the immediate Manager redirect 🚨
    
    # We now render the staff_hub.html (Tiles) directly for everyone.
    return render(request, "checklists/staff_hub.html", {})


@login_required
def daily_view_content(request):
    """
    Handles content filtering and dynamic auto-creation.
    (This is the checklist list view linked from the Operational Hub)
    """
    user_groups = request.user.groups.values_list('name', flat=True)
    operational_date = get_operational_date() 
    sessions_data = [] # Initialize sessions_data

    # --- DYNAMIC AUTO-CREATION LOGIC ---
    all_active_templates = ChecklistTemplate.objects.filter(is_active=True)
    
    for template in all_active_templates:
        shift_name = template.name.split(' - ')[-1].replace('Check List', '').strip()
        if not shift_name:
             shift_name = template.name

        try:
            ChecklistSession.objects.get_or_create(
                template=template,
                date=operational_date,
                defaults={'shift_name': shift_name, 'created_by': request.user,}
            )
        except Exception as e:
            print(f"ERROR: Session creation failed for {template.name} on {operational_date}. Reason: {e}")
            pass

    # --- Role-based session filtering ---
    if 'Supervisor' in user_groups or 'Manager' in user_groups: 
        sessions_qs = ChecklistSession.objects.filter(date=operational_date)
    elif 'Bartender' in user_groups:
        sessions_qs = ChecklistSession.objects.filter(date=operational_date, template__category='bar')
    elif 'Security' in user_groups:
        sessions_qs = ChecklistSession.objects.filter(date=operational_date, template__category='security')
    else:
        sessions_qs = ChecklistSession.objects.none()

    # --- Calculate completion status ---
    for session in sessions_qs:
        actionable_items = session.template.items.filter(type='item')
        total_items = actionable_items.count()
        done_responses = ItemResponse.objects.filter(
            session=session,
            status='done',
            item__type='item'  # only count non-heading items
        ).count()
        is_completed = (total_items > 0 and done_responses == total_items)
        sessions_data.append({'session': session, 'is_completed': is_completed})


    # FIX: Render the list template (session_list.html)
    return render(request, "checklists/session_list.html", {"sessions": sessions_data, "today": operational_date,})


@login_required
def session_detail(request, session_id):
    """Display a session with its item responses, creating missing responses."""
    session = get_object_or_404(ChecklistSession, pk=session_id)
    
    # Ensure all items in the template have a placeholder response
    for item in session.template.items.all().order_by("order"):
        if item.type == 'item':
            ItemResponse.objects.get_or_create(
                item=item,
                session=session,
                defaults={"status": "pending", "performed_by": None}
            )
        else:
            # Heading — auto-complete
            ItemResponse.objects.get_or_create(
                item=item,
                session=session,
                defaults={"status": "done", "performed_by": None}
            )


    # Fetch responses (the single row for each task/heading)
    responses = ItemResponse.objects.filter(session=session).select_related("item", "performed_by").order_by("item__order")

    return render(request, "checklists/session_detail.html", {"session": session, "responses": responses,})


@login_required
def complete_item(request, session_id, item_id):
    """Marks a specific ItemResponse as complete or pending."""
    session = get_object_or_404(ChecklistSession, id=session_id)
    item = get_object_or_404(ChecklistItem, id=item_id)

    try:
        response = ItemResponse.objects.get(session=session, item=item)
    except ItemResponse.DoesNotExist:
        messages.error(request, "Error: Task record not found. Please refresh the page.")
        return redirect('checklists:session_detail', session_id=session_id) 

    user_is_manager_or_supervisor = is_manager_or_supervisor(request.user)
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "complete":
            response.status = "done"
            response.performed_by = request.user
        elif action == "pending":
            if not user_is_manager_or_supervisor:
                messages.error(request, "Only Managers or Supervisors can revert a task to pending.")
                return redirect('checklists:session_detail', session_id=session_id)
            response.status = "pending"
            response.performed_by = None
        
        response.performed_at = timezone.now()
        response.save()
        messages.success(request, f"Task '{response.item.name}' status updated to {response.status.title()}.")

        return redirect(f"{reverse('checklists:session_detail', args=[session_id])}#item-{item_id}")
    
    return redirect('checklists:session_detail', session_id=session_id)


# ----------------------------------------------------------
# --- TEMPLATE MANAGEMENT VIEWS ---
# ----------------------------------------------------------

@login_required
def template_list(request):
    if not check_manager_access(request): return redirect('manager_dashboard')
    templates = ChecklistTemplate.objects.all().order_by('-created_at')
    return render(request, 'checklists/template_list.html', {'templates': templates})

@login_required
def template_add(request):
    from .forms import ChecklistTemplateForm 
    if not check_manager_access(request): return redirect('manager_dashboard')
    if request.method == 'POST':
        form = ChecklistTemplateForm(request.POST)
        if form.is_valid():
            new_template = form.save(commit=False)
            new_template.created_by = request.user
            new_template.save()
            messages.success(request, f"Checklist template '{new_template.name}' created successfully!")
            return redirect('checklists:template_list')
    else:
        form = ChecklistTemplateForm()
    return render(request, 'checklists/template_form.html', {'form': form, 'action': 'Add'})

@login_required
def template_edit(request, template_id):
    from .forms import ChecklistTemplateForm
    if not check_manager_access(request): return redirect('manager_dashboard')
    template = get_object_or_404(ChecklistTemplate, pk=template_id)
    if request.method == 'POST':
        form = ChecklistTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f"Template '{template.name}' updated successfully.")
            return redirect('checklists:template_list')
    else:
        form = ChecklistTemplateForm(instance=template)
    return render(request, 'checklists/template_form.html', {'form': form, 'action': 'Edit', 'template': template})

@login_required
def template_delete(request, template_id):
    if not check_manager_access(request): return redirect('manager_dashboard')
    template = get_object_or_404(ChecklistTemplate, pk=template_id)
    if request.method == 'POST':
        template_name = template.name
        template.delete()
        messages.success(request, f"Template '{template_name}' and all associated history have been permanently deleted.")
        return redirect('checklists:template_list')
    return render(request, 'checklists/template_confirm_delete.html', {'template': template})


# ----------------------------------------------------------
# --- CHECKLIST ITEM MANAGEMENT VIEWS ---
# ----------------------------------------------------------

@login_required
def item_list(request, template_id):
    if not check_manager_access(request): return redirect('manager_dashboard')
    template = get_object_or_404(ChecklistTemplate, pk=template_id)
    items = template.items.all().order_by('order', 'name')
    return render(request, 'checklists/item_list.html', {'template': template, 'items': items,})

@login_required
def item_add(request, template_id):
    from .forms import ChecklistItemForm # Local import
    if not check_manager_access(request): return redirect('manager_dashboard')
    template = get_object_or_404(ChecklistTemplate, pk=template_id)
    if request.method == 'POST':
        form = ChecklistItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.template = template
            item.save()
            messages.success(request, f"Item '{item.name}' added to {template.name}.")
            return redirect('checklists:item_list', template_id=template_id)
    else:
        initial_order = template.items.count() + 1
        form = ChecklistItemForm(initial={'order': initial_order})
    return render(request, 'checklists/item_form.html', {'form': form, 'template': template, 'action': 'Add'})

@login_required
def item_edit(request, template_id, item_id):
    from .forms import ChecklistItemForm # Local import
    if not check_manager_access(request): return redirect('manager_dashboard')
    template = get_object_or_404(ChecklistTemplate, pk=template_id)
    item = get_object_or_404(template.items, pk=item_id)
    if request.method == 'POST':
        form = ChecklistItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"Item '{item.name}' updated successfully.")
            return redirect("checklists:item_list", template_id=template_id)
    else:
        form = ChecklistItemForm(instance=item)
    return render(request, 'checklists/item_form.html', {'form': form, 'template': template, 'action': 'Edit', 'item': item,})

@login_required
def item_delete(request, template_id, item_id):
    if not check_manager_access(request): return redirect('manager_dashboard')
    template = get_object_or_404(ChecklistTemplate, pk=template_id)
    item = get_object_or_404(template.items, pk=item_id)
    if request.method == 'POST':
        name = item.name
        item.delete()
        messages.success(request, f"Item '{name}' successfully removed from {template.name}.")
        return redirect("checklists:item_list", template_id=template_id)
    return render(request, 'checklists/item_confirm_delete.html', {'template': template, 'item': item,})


# ----------------------------------------------------------
# --- INCIDENT & MAINTENANCE LOGS (PLACEHOLDERS) ---
# ----------------------------------------------------------
@login_required
def log_incident(request):
    """
    Renders the form, but actual logic is housed in reporting_views.py
    """
    from .forms import IncidentLogForm
    form = IncidentLogForm()
    return render(request, 'checklists/incident_log_form.html', {'form': form})

@login_required
def maintenance_log_create(request):
    """Create a new maintenance log (similar to incident_log)."""
    from .forms import MaintenanceLogForm
    form = MaintenanceLogForm()
    return render(request, 'checklists/maintenance_log_form.html', {'form': form})

