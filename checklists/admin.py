# checklists/admin.py (Revised file)
from django.contrib import admin
from .models import ChecklistTemplate, ChecklistItem, ChecklistSession, ItemResponse, IncidentLog, MaintenanceLog

class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 1

@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = [ChecklistItemInline]

@admin.register(ChecklistSession)
class ChecklistSessionAdmin(admin.ModelAdmin):
    list_display = ('template', 'shift_name', 'date', 'is_closed')
    list_filter = ('is_closed', 'template')

@admin.register(ItemResponse)
class ItemResponseAdmin(admin.ModelAdmin):
    list_display = ('item', 'session', 'performed_by', 'status', 'performed_at')
    list_filter = ('status',)

# 🚨 FIX: Explicitly register ChecklistItem 🚨
@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'order')
    list_filter = ('template',)
    search_fields = ('name',)
    
    # We will use this list display, but ensure we keep the name consistent:
    # URL name will be: admin:checklists_checklistitem_changelist

@admin.register(IncidentLog)
class IncidentLogAdmin(admin.ModelAdmin):
    list_display = ('operational_date', 'incident_type', 'location', 'reported_by', 'timestamp')
    list_filter = ('incident_type', 'operational_date', 'location')
    search_fields = ('location', 'summary', 'persons_involved', 'action_taken')

@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('operational_date', 'reported_by', 'title', 'location', 'timestamp')
    list_filter = ('operational_date', 'location', 'reported_by')
    search_fields = ('title', 'description', 'location', 'reported_by__username')
    ordering = ('-operational_date',)
