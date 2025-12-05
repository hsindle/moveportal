# events/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q

# --- Event Category Model ---
class EventCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color_code = models.CharField(max_length=7, default='#3366ff', help_text="Hex code for calendar color.")

    def __str__(self):
        return self.name
        
    class Meta:
        verbose_name = "Event Category"
        verbose_name_plural = "Event Categories"


# --- Promoter Model ---
class Promoter(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

# --- Event Model ---
class Event(models.Model):
    name = models.CharField(max_length=200) 
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, blank=True)
    promoter = models.ForeignKey(Promoter, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True) 
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Set to False to hide from public/main calendar view.")
    epk_link = models.URLField(max_length=500, blank=True, null=True, verbose_name="EPK / Press Kit Link")
    hospitality_rider = models.TextField(blank=True, null=True)
    technical_rider = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True, verbose_name="Internal Notes")
    team = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='scheduled_events', blank=True,
        help_text="Select staff members involved in this event."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['start_date']
        verbose_name = "Event"
        verbose_name_plural = "Events"
        
    def __str__(self):
        return f"{self.name} ({self.start_date.strftime('%Y-%m-%d') if self.start_date else 'No Date'})"
    
    def get_absolute_url(self):
        return reverse('events:event_detail', args=[self.pk])

# --- Event Artwork Model ---
class EventArtwork(models.Model):
    """Stores artwork files related to a specific event."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='artwork')
    # 🚨 FIX: These fields must exist in the model for the form to load 🚨
    title = models.CharField(max_length=100) 
    image = models.ImageField(upload_to='event_artwork/', help_text="Artwork file for marketing or production.")
    
    def __str__(self):
        return f"{self.title} for {self.event.name}"