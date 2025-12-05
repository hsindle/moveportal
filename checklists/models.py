# checklists/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class ChecklistTemplate(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # 🚨 FIX: Added 'management' category 🚨
    CATEGORY_CHOICES = [
        ('security', 'Security'),
        ('bar', 'Bar'),
        ('management', 'Management'), # NEW Category
    ]
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='security' 
    )

    def __str__(self):
        return self.name

class ChecklistItem(models.Model):
    ITEM_TYPES = [
        ('item', 'Item'),
        ('heading', 'Heading'),
    ]

    template = models.ForeignKey(
        ChecklistTemplate, on_delete=models.CASCADE, related_name='items'
    )
    name = models.CharField(max_length=100, default="Unnamed Item")
    order = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=10, choices=ITEM_TYPES, default='item')
    
    # NEW: Reference parent heading
    heading = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='subitems'
    )

    def __str__(self):
        return self.name



class ChecklistSession(models.Model):
    template = models.ForeignKey(
        ChecklistTemplate, 
        on_delete=models.CASCADE, 
        related_name='sessions'
    )
    shift_name = models.CharField(max_length=100)
    date = models.DateField(default=timezone.now)
    is_closed = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        unique_together = ('template', 'date')

    def __str__(self):
        return f"{self.template.name} - {self.shift_name} ({self.date})"

    @staticmethod
    def can_create_today(template):
        return not template.sessions.filter(date=timezone.localdate()).exists()

class ItemResponse(models.Model):
    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE)
    session = models.ForeignKey(ChecklistSession, on_delete=models.CASCADE)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('done', 'Done')], default='pending')
    notes = models.TextField(blank=True)
    performed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('item', 'session')   # ← remove performed_by if it exists

    
class IncidentLog(models.Model):
    """Stores a record of an incident, filled out by staff/management."""
    
    # Metadata
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='incidents_reported'
    )
    timestamp = models.DateTimeField(default=timezone.now)
    operational_date = models.DateField(default=timezone.localdate) # For reporting/grouping
    
    # Core Fields
    incident_type = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    persons_involved = models.TextField(blank=True, verbose_name="Names/Descriptions of Persons Involved")
    summary = models.TextField(verbose_name="Detailed Summary of Incident")
    action_taken = models.TextField(verbose_name="Action Taken by Staff")
    
    # State
    is_locked = models.BooleanField(default=True) # Lock immediately upon creation
    
    def __str__(self):
        return f"Incident {self.id}: {self.incident_type} ({self.operational_date})"
    
class MaintenanceLog(models.Model):
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='maintenance_reports'
    )
    timestamp = models.DateTimeField(default=timezone.now)
    operational_date = models.DateField(default=timezone.localdate)

    title = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True)
    persons_involved = models.TextField(blank=True)
    description = models.TextField(blank=True)
    action_taken = models.TextField(blank=True)

    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.location} - {self.title[:30]}"
