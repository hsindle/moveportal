from django.urls import path
from . import views
from . import reporting_views

app_name = "checklists"

urlpatterns = [
    # Daily operations
    path("", views.home, name="home"),  # staff_hub.html (tiles)
    path("daily-view/", views.daily_view_content, name="daily_view_content"),
    path("session/<int:session_id>/", views.session_detail, name="session_detail"),
    path("session/<int:session_id>/complete/<int:item_id>/", views.complete_item, name="complete_item"),

    # Template management
    path("templates/", views.template_list, name="template_list"),
    path("templates/add/", views.template_add, name="template_add"),
    path("templates/edit/<int:template_id>/", views.template_edit, name="template_edit"),
    path("templates/delete/<int:template_id>/", views.template_delete, name="template_delete"),

    # Checklist items
    path("templates/<int:template_id>/items/", views.item_list, name="item_list"),
    path("templates/<int:template_id>/items/add/", views.item_add, name="item_add"),
    path("templates/<int:template_id>/items/edit/<int:item_id>/", views.item_edit, name="item_edit"),
    path("templates/<int:template_id>/items/delete/<int:item_id>/", views.item_delete, name="item_delete"),

    # Reporting & incidents
    path("history/", reporting_views.checklist_history, name="history_dashboard"),
    path("incidents/", reporting_views.incident_history, name="incident_history"), 
    path("incident/log/", reporting_views.log_incident, name="log_incident"),
    path("session/<int:session_id>/completion/", reporting_views.session_completion_detail, name="session_completion_detail"),
    path("history/session/<int:session_id>/", reporting_views.session_history, name="session_history"),
    path('maintenance/', reporting_views.maintenance_log_create, name='log_maintenance'),
    path('maintenance/history/', reporting_views.maintenance_history, name='maintenance_history'),
]
