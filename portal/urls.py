from django.contrib import admin
from django.urls import path, include
from . import views
from django.urls import reverse_lazy
from django.conf import settings
from django.conf.urls.static import static


# Optional: redirect after login using namespaced URL
LOGIN_REDIRECT_URL = '/checklists/'  
LOGOUT_REDIRECT_URL = '/accounts/login/'  # Optional, for logout

urlpatterns = [
    # 🚨 FIX: This line MUST be present to handle the root path (/) 🚨
    path('', include('checklists.urls')), 
    
    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', views.staff_register, name='register'),

    # Manager dashboard and user management 
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/add-user/', views.manager_add_user, name='manager_add_user'),
    path('manager/users/', views.manager_user_list, name='manager_user_list'),
    path('manager/users/edit/<int:user_id>/', views.manager_edit_user, name='manager_edit_user'),
    path('manager/users/delete/<int:user_id>/', views.manager_delete_user, name='manager_delete_user'),

    #  Include checklists app URLs under /checklists/ namespace
    path('checklists/', include('checklists.urls', namespace='checklists')),

    #   Rota Related
    path('rota/', include('rota.urls')),

    # Events Calander Related
    path("events/", include("events.urls")),

    # Training Related
    path('training/', include('training.urls', namespace='training')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
