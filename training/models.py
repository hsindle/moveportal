# training/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import Group # Needed to link courses to roles
from datetime import timedelta

# --- 1. Course Model (The Training Module) ---
class Course(models.Model):
    """Defines a training module, its video, and the roles required to complete it."""
    
    title = models.CharField(max_length=200)
    # The URL link to the training video (e.g., YouTube embed link)
    video_url = models.URLField(max_length=500, blank=True, null=True)
    
    # 🚨 CRITICAL: Role Assignment (M2M to Groups) 🚨
    required_for_groups = models.ManyToManyField(
        Group, related_name='required_courses', 
        help_text="Groups that must complete this training (e.g., Security, Bartender)."
    )
    
    # Scheduling Flag (for recurring annual training like Fire Safety)
    is_recurring = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

# --- 2. Question Model (For the Quiz) ---
class Question(models.Model):
    """A single multiple-choice question linked to a course."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    correct_answer = models.CharField(max_length=255)
    
    # Options are stored as a JSON field (CharField for simplicity in this MVP)
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255, blank=True)
    option_d = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Q{self.id}: {self.text[:40]}..."

# --- 3. User Attempt Model (Tracking Completion History) ---
class UserAttempt(models.Model):
    """Tracks a user's attempt and completion status for a specific course."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='training_attempts')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    # Completion status
    is_passed = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    
    # Date tracking
    date_completed = models.DateTimeField(null=True, blank=True)
    renewal_due_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        # Ensures a user cannot pass the same course multiple times (unless recurring)
        unique_together = ('user', 'course')
        verbose_name = "Training Completion Record"
        verbose_name_plural = "Training Completion Records"
        
    def __str__(self):
        return f"{self.user.username} | {self.course.title} | {'Passed' if self.is_passed else 'Failed'}"
    
    def save(self, *args, **kwargs):
        # Automatically set renewal date if the course is recurring and passed
        if self.course.is_recurring and self.is_passed and self.date_completed:
            # Assuming annual renewal (1 year interval)
            self.renewal_due_date = self.date_completed + timedelta(days=365)
        super().save(*args, **kwargs)

class OnboardingDocument(models.Model):
    """
    Tracks initial HR compliance and essential start-up information.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='onboarding_doc'
    )
    
    # 1. Personal/Contact Details
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)
    
    # 2. Financial Details
    bank_name = models.CharField(max_length=100)
    account_holder_name = models.CharField(max_length=100)
    sort_code = models.CharField(max_length=10)
    account_number = models.CharField(max_length=20)

    # 3. Documents (File Uploads)
    right_to_work_proof = models.FileField(
        upload_to='compliance/rtw/', 
        verbose_name="Right to Work Proof (Passport/Visa)",
        help_text="Required document upload."
    )
    p45_document = models.FileField(
        upload_to='compliance/p45/', 
        verbose_name="P45 Document (Optional)",
        null=True, blank=True
    )
    
    # 4. Completion Status
    is_completed = models.BooleanField(default=False)
    date_submitted = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Onboarding for {self.user.get_full_name()}"