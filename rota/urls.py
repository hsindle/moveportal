# rota/urls.py
from django.urls import path
from . import views

app_name = 'rota'

urlpatterns = [
    # Main Rota Viewer Page
    path('', views.rota_view, name='rota_view'),
    
    path('admin/', views.shift_admin, name='shift_admin'),
    path('admin/edit/<int:shift_id>/', views.shift_edit, name='shift_edit'),
    path('admin/add/', views.shift_edit, name='shift_add'),
    path('admin/delete/<int:shift_id>/', views.shift_delete, name='shift_delete'),
]