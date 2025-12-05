from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # The default AbstractUser already includes first_name, last_name, and email.

    is_deleted = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)
    
    # 🚨 REMOVED: Old 'role' CharField and ROLE_CHOICES (using Groups instead) 🚨

    # --- USER REPRESENTATION OVERRIDES (Kept, as they are crucial) ---
    
    def __str__(self):
        """Prioritizes full name for display, falls back to username."""
        full_name = f"{self.first_name}{self.last_name}".strip()
        if full_name:
            return full_name
        return self.username

    def get_full_name(self):
        """Returns the first_name plus the last_name, with a space in between."""
        return f"{self.first_name}{self.last_name}".strip()
        
    def get_short_name(self):
        """Returns the first name."""
        return self.first_name

    # 🚨 REMOVED: Old role checkers (is_manager, is_supervisor, etc.) 🚨
    # Access checks now use `request.user.groups.filter(name='Manager').exists()`
    pass # No new fields or methods needed here.