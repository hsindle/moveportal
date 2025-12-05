# rota/admin.py

from django.contrib import admin
from .models import Shift

# Define how the Shift model should be displayed and managed in the admin
class ShiftAdmin(admin.ModelAdmin):
    # Fields to display in the main list table
    list_display = ('user', 'operational_date', 'start_time', 'end_time', 'notes', 'position') 
    
    # Fields to link to the edit page
    list_display_links = ('user', 'operational_date',)
    
    # Filters for the right sidebar (e.g., filter by date, position, or group)
    list_filter = ('operational_date', 'position', 'user__groups__name')
    
    # Fields to search across
    search_fields = ('user__first_name', 'user__last_name', 'notes')
    
    # Grouping fields on the edit page for better layout
    fieldsets = (
        ('Staff and Date', {
            'fields': ('user', 'operational_date',)
        }),
        ('Time and Details', {
            # Note: 'position' should be optional in your model for this to work with the custom form.
            'fields': ('start_time', 'end_time', 'notes', 'position')
        }),
    )

# Register the model
admin.site.register(Shift, ShiftAdmin)