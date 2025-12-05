# checklists/data_access.py
# This module centralizes data logic to break circular dependencies.
from datetime import date
from itertools import groupby
from .models import ChecklistTemplate, ChecklistSession, ItemResponse, IncidentLog
from django.utils import timezone

def get_incident_history_data(request):
    """Fetches, filters, and groups IncidentLog data for the dashboard."""
    
    # Get filters from GET request
    incident_type = request.GET.get('incident_type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    incidents = IncidentLog.objects.all().order_by('-timestamp')

    # Apply Filters
    if incident_type:
        incidents = incidents.filter(incident_type__icontains=incident_type)
    if start_date:
        incidents = incidents.filter(operational_date__gte=start_date)
    if end_date:
        incidents = incidents.filter(operational_date__lte=end_date)
        
    incidents_data = list(incidents.select_related('reported_by'))
    incidents_data.sort(key=lambda x: x.operational_date, reverse=True)
    
    grouped_incidents = []
    for date_key, group in groupby(incidents_data, key=lambda x: x.operational_date):
        grouped_incidents.append({
            'date': date_key,
            'incidents': list(group)
        })
        
    all_incident_types = IncidentLog.objects.values_list('incident_type', flat=True).distinct().order_by('incident_type')

    return {
        'grouped_incidents': grouped_incidents,
        'incident_types': all_incident_types,
        'selected_incident_type': incident_type,
        'start_date': start_date,
        'end_date': end_date,
    }