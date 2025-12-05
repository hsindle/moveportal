# events/urls.py (Final version, ensuring all paths exist)
from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # Main Calendar / Dashboard
    path("", views.event_calendar, name="event_calendar"), 
    
    # Event Management
    path('list/', views.event_list, name='event_list'),
    path('add/', views.event_create, name='event_add'),
    
    # Day View: For clicking a date on the calendar (e.g., /events/day/2025-12-25/)
    path('day/<str:date_str>/', views.event_day_view, name='event_day_view'),
    
    # Event Detail & Edit
    path('<int:event_id>/', views.event_detail, name='event_detail'),
    path('<int:event_id>/edit/', views.event_edit, name='event_edit'),
    path('<int:event_id>/delete/', views.event_delete, name='event_delete'),
    
    # API Endpoint 
    path('api/events/', views.event_list_api, name='event_list_api'),

    # --- Promoter Management ---
    path('promoters/', views.promoter_list, name='promoter_list'),
    path('promoters/add/', views.promoter_edit, name='promoter_add'),
    path('promoters/edit/<int:promoter_id>/', views.promoter_edit, name='promoter_edit'),
    path('promoters/delete/<int:promoter_id>/', views.promoter_delete, name='promoter_delete'),
    
    # --- Category Management ---
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_edit, name='category_add'),
    path('categories/edit/<int:category_id>/', views.category_edit, name='category_edit'),
]