from django.db import models
from django.conf import settings
from django.utils import timezone

class Shift(models.Model):
    """Stores a single instance of a scheduled shift."""
    
    # Link to user and date information
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='shifts'
    )
    operational_date = models.DateField() # The start date of the shift
    
    # Time details
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True) # 🚨 FIX: Must allow NULL for 'CLOSE' 🚨
    
    # Shift details
    position = models.CharField(max_length=50, blank=True, null=True) 
    notes = models.TextField(blank=True, null=True)

    class Meta:
        # Ensures a user cannot be scheduled for two different shifts on the same day.
        unique_together = ('user', 'operational_date')
        ordering = ['operational_date', 'start_time']

    def __str__(self):
        return f"{self.user.get_full_name()} | {self.operational_date} ({self.start_time})"