# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    # 🚨 FIX 1: Remove the obsolete 'Role Information' fieldset 🚨
    # We manage roles via the 'groups' field now (which is included in UserAdmin.fieldsets)
    fieldsets = UserAdmin.fieldsets
    
    # 🚨 FIX 2: Remove the obsolete 'Role Information' add_fieldset 🚨
    add_fieldsets = UserAdmin.add_fieldsets
    

admin.site.register(CustomUser, CustomUserAdmin)