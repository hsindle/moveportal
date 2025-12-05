# events/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q
from datetime import datetime, date, timedelta

# Local Models and Forms
from .models import Event, EventArtwork
from .forms import EventForm, EventArtworkForm, Promoter,EventCategory # Ensure both are imported


# --- Helper to check Manager/Supervisor access ---
def is_manager_or_supervisor(user):
    """Return True if user is Manager or Supervisor."""
    return user.groups.filter(name__in=["Manager", "Supervisor"]).exists()


@login_required
def event_calendar(request):
    """Renders the main calendar view (Default app landing)."""
    # Note: Access control is handled here to prevent staff from seeing the full calendar first.
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied to full calendar view.")
        return redirect('events:event_list')

    return render(request, "events/event_calendar.html", {})


@login_required
def event_day_view(request, date_str):
    """Renders all events scheduled for a specific day."""
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('events:event_list')
        
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return redirect('events:event_calendar')

    # Fetch events starting or ending on this day
    events = Event.objects.filter(
        Q(start_date__date=target_date) | Q(end_date__date=target_date)
    ).order_by('start_date')

    context = {
        'target_date': target_date,
        'events': events,
    }
    return render(request, "events/event_day_view.html", context)


@login_required
def event_list(request):
    """View to list all events (Manager/Supervisor access required)."""
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('checklists:home') # Redirect staff back to hub
        
    events = Event.objects.all().order_by('-start_date')
    context = {
        'events': events,
    }
    return render(request, 'events/event_list.html', context)


@login_required
def event_detail(request, event_id):
    """Detailed view of a single event, including riders and artwork."""
    event = get_object_or_404(Event, pk=event_id)
    
    # Artwork Form (for adding new artwork)
    if request.method == 'POST':
        artwork_form = EventArtworkForm(request.POST, request.FILES)
        if artwork_form.is_valid():
            artwork = artwork_form.save(commit=False)
            artwork.event = event
            artwork.save()
            messages.success(request, "Artwork uploaded successfully.")
            return redirect('events:event_detail', event_id=event_id)
    else:
        artwork_form = EventArtworkForm()
        
    context = {
        "event": event,
        "artwork_form": artwork_form,
    }
    return render(request, "events/event_detail.html", context)


@login_required
def event_create(request):
    """View for managers to add a new event, pre-populating date from calendar click."""
    from .forms import EventForm
    
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('checklists:home')
    
    # 🚨 FIX: Check for pre-fill date from the URL 🚨
    initial_data = {}
    if request.method == 'GET':
        prefill_date = request.GET.get('date')
        if prefill_date:
            try:
                # Convert YYYY-MM-DD string to a datetime object for the DateTimeInput field
                initial_start_time = datetime.strptime(prefill_date, '%Y-%m-%d')
                initial_data['start_date'] = initial_start_time
            except ValueError:
                # Ignore if the date format is wrong
                pass
        
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES) 
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            form.save_m2m() 
            messages.success(request, f"Event '{event.name}' created successfully.")
            return redirect('events:event_list')
    else:
        # Pass initial data on GET request
        form = EventForm(initial=initial_data) 
        
    context = {
        'form': form,
        'page_title': 'Create New Event',
    }
    return render(request, 'events/event_form.html', context)


@login_required
def event_edit(request, event_id):
    """View for managers to edit an existing event."""
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('checklists:home')
        
    event_instance = get_object_or_404(Event, pk=event_id)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event_instance)
        if form.is_valid():
            form.save()
            
            # 🚨 CRITICAL FIX: Save Many-to-Many relationships 🚨
            form.save_m2m()
            
            messages.success(request, f"Event '{event_instance.name}' updated successfully.")
            return redirect('events:event_detail', event_id=event_id)
    else:
        form = EventForm(instance=event_instance)
        
    context = {
        'form': form,
        'page_title': f"Edit Event: {event_instance.name}",
        'event': event_instance,
    }
    return render(request, "events/event_form.html", context)


# --- API Endpoint ---
@login_required
def event_list_api(request):
    from django.urls import reverse
    
    # 🚨 FIX: Use select_related to prefetch the category color 🚨
    events = Event.objects.filter(is_active=True, start_date__isnull=False).select_related('category') 
    
    data = []
    for event in events:
        # Safely determine category name and color
        category_name = event.category.name if event.category else 'Misc'
        # 🚨 FIX: Ensure a fallback color is used if category is None 🚨
        category_color = event.category.color_code if event.category and event.category.color_code else '#cccccc'
        
        data.append({
            "id": event.id,
            "title": f"{event.name} ({category_name})",
            "start": event.start_date.isoformat(),
            "end": event.end_date.isoformat() if event.end_date else None,
            "url": reverse('events:event_detail', args=[event.id]),
            "color": category_color, # Pass the color code
        })
    return JsonResponse(data, safe=False)


@login_required
def event_delete(request, event_id):
    """View for managers to confirm and delete an existing event."""
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied. Only Managers/Supervisors can delete events.")
        return redirect('events:event_list')
        
    event = get_object_or_404(Event, pk=event_id)
    
    if request.method == 'POST':
        # Execute the deletion
        event_name = event.name
        event.delete()
        messages.success(request, f"Event '{event_name}' has been permanently deleted.")
        return redirect('events:event_list')
        
    # Render confirmation page (GET request)
    context = {
        'event': event,
    }
    return render(request, 'events/event_confirm_delete.html', context)

@login_required
def promoter_list(request):
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('events:event_list')
    
    promoters = Promoter.objects.all().order_by('name')
    return render(request, 'events/promoter_list.html', {'promoters': promoters})

@login_required
def promoter_edit(request, promoter_id=None):
    from .forms import PromoterForm # Local import
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('events:event_list')
        
    instance = get_object_or_404(Promoter, pk=promoter_id) if promoter_id else None
    
    if request.method == 'POST':
        form = PromoterForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Promoter '{form.cleaned_data['name']}' saved successfully.")
            return redirect('events:promoter_list')
    else:
        form = PromoterForm(instance=instance)
        
    return render(request, 'events/promoter_form.html', {'form': form, 'page_title': 'Edit Promoter' if instance else 'Add New Promoter'})

# --- CATEGORY MANAGEMENT VIEWS (Color Coding) ---

@login_required
def category_list(request):
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('events:event_list')
    
    categories = EventCategory.objects.all().order_by('name')
    return render(request, 'events/category_list.html', {'categories': categories})

@login_required
def category_edit(request, category_id=None):
    from .forms import EventCategoryForm # Local import
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied.")
        return redirect('events:event_list')
        
    instance = get_object_or_404(EventCategory, pk=category_id) if category_id else None
    
    if request.method == 'POST':
        form = EventCategoryForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Category '{form.cleaned_data['name']}' saved successfully.")
            return redirect('events:category_list')
    else:
        form = EventCategoryForm(instance=instance)
        
    return render(request, 'events/category_form.html', {'form': form, 'page_title': 'Edit Category' if instance else 'Add New Category'})

@login_required
def promoter_delete(request, promoter_id):
    """View to confirm and execute the archiving (soft delete) of a promoter."""
    if not is_manager_or_supervisor(request.user):
        messages.error(request, "Access denied. Only Managers/Supervisors can delete promoters.")
        return redirect('events:promoter_list')
        
    promoter = get_object_or_404(Promoter, pk=promoter_id)
    
    if request.method == 'POST':
        promoter_name = promoter.name
        
        # 🚨 FIX 3: ARCHIVE (Soft Delete) Logic 🚨
        promoter.is_active = False # Set the flag to hide the promoter
        promoter.save()
        
        # NOTE: We no longer need the check for linked events, as archiving is non-destructive.
        
        messages.success(request, f"Promoter '{promoter_name}' has been successfully archived and removed from the active list.")
        return redirect('events:promoter_list')
        
    # Render Confirmation Page (GET request)
    return render(request, 'events/promoter_confirm_delete.html', {
        'promoter': promoter,
    })