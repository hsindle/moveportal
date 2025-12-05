# training/urls.py
from django.urls import path
from . import views

app_name = 'training'

urlpatterns = [
    path('', views.training_dashboard, name='training_dashboard'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/start/', views.course_start, name='course_start'),
    path('course/<int:course_id>/submit/', views.quiz_submit, name='quiz_submit'),
    
    # Manager Admin Link (Redirects to Django Admin for management)
    path('admin/', views.manager_training_list, name='manager_training_list'), 
    path('admin/add/', views.course_admin_edit, name='course_admin_add'),
    path('admin/edit/<int:course_id>/', views.course_admin_edit, name='course_admin_edit'),
    path('user/<int:user_id>/history/', views.user_training_history, name='user_training_history'),
    path('onboarding/', views.onboarding_start, name='onboarding_start'),
]