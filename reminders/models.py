from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import pytz
from datetime import datetime

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    timezone = models.CharField(
        max_length=32,
        choices=[(tz, tz) for tz in pytz.common_timezones],
        default='UTC'
    )

    def __str__(self):
        return self.user.username
    

class Tag(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tags")
    
    def __str__(self):
        return self.name
    
    
class Reminder(models.Model):
    
    def reminder_image_path(instance, filename):
        """Generate a unique path for each uploaded image."""
        # Format: uploads/user_<id>/reminder_<id>/<filename>
        return f'uploads/user_{instance.user.id}/reminder_{instance.id}/{filename}'
     
    # Early Reminder Options
    EARLY_REMINDER_CHOICES = [
        ('none', 'None'),
        ('5min', '5 Minutes Before'),
        ('10min', '10 Minutes Before'),
        ('custom', 'Custom'),
    ]

    # Repeat Options
    REPEAT_CHOICES = [
        ('never', 'Never'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekdays', 'Weekdays'),
        ('weekends', 'Weekends'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Biweekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Every 3 Months'),
        ('biannually', 'Every 6 Months'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]

    # Priority Levels
    PRIORITY_CHOICES = [
        ('none', 'None'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    is_all_day = models.BooleanField(default=False) 
    early_reminder = models.CharField(max_length=20, choices=EARLY_REMINDER_CHOICES, default='none')
    custom_early_reminder = models.DurationField(null=True, blank=True)
    repeat = models.CharField(max_length=20, choices=REPEAT_CHOICES, default='never')
    repeat_end_date = models.DateField(null=True, blank=True)
    custom_repeat_interval = models.JSONField(null=True, blank=True)  
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_flagged = models.BooleanField(default=False)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='none')
    notification_preference = models.CharField(
        max_length=10,
        choices=[('email', 'Email'), ('push', 'Push'), ('both', 'Both')],
        default='both'
    )
    location = models.CharField(max_length=255, blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="reminders")
    image = models.ImageField(upload_to=reminder_image_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

    def get_local_scheduled_time(self, user):
        """
        Get the reminder's scheduled time in the user's local timezone.
        If there's no date/time set, return None.
        """

        if not self.date:
            return None
        
        if self.is_all_day or not self.time:
            time_part = datetime.min.time()
        else:
            time_part = self.time
        
        utc_time = datetime.combine(self.date, time_part)
        utc_time = pytz.UTC.localize(utc_time)
        
        try:
            user_profile, created = UserProfile.objects.get_or_create(user=user, defaults={'timezone': 'UTC'})
            user_timezone = pytz.timezone(user_profile.timezone)
        except Exception:
            user_timezone = pytz.UTC
        
        local_time = utc_time.astimezone(user_timezone)
        return local_time

    def set_local_scheduled_time(self, user, local_time):
        """
        Set the reminder's date and time fields based on the provided local time.
        """    
        try:
            user_profile, created = UserProfile.objects.get_or_create(user=user, defaults={'timezone': 'UTC'})
            user_timezone = pytz.timezone(user_profile.timezone)
        except Exception:
            user_timezone = pytz.UTC
        
        if isinstance(local_time, str):
            try:
                local_time = datetime.fromisoformat(local_time.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                local_time = datetime.now()
       
        if local_time.tzinfo is None:
            local_dt = user_timezone.localize(local_time, is_dst=None)
        else:
            local_dt = local_time
        
        utc_time = local_dt.astimezone(pytz.UTC)
        
        self.date = utc_time.date()
        if not self.is_all_day:
            self.time = utc_time.time()
        else:
            self.time = None

    def mark_as_completed(self):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()


class SubTask(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    is_all_day = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_flagged = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=20, 
        choices=Reminder.PRIORITY_CHOICES, 
        default='none')
    tags = models.ManyToManyField(Tag, blank=True, related_name="subtasks")
    reminder = models.ForeignKey(Reminder, on_delete=models.CASCADE, related_name="subtasks")
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    
    def __str__(self):
        return self.title
    
    def mark_as_completed(self):
        self.is_completed = True
        self.completed_at = timezone.now
        self.save()

class SharedReminder(models.Model):
    reminder = models.ForeignKey(Reminder, on_delete=models.CASCADE)
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_reminders')
    permissions = models.CharField(
        max_length=4,
        choices=[('view', 'View'), ('edit', 'Edit')],
        default='view'
    )
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reminder', 'shared_with')

    def __str__(self):
        return f"Shared {self.reminder.title} with {self.shared_with.username} ({self.permissions})"

class DeviceToken(models.Model):
    DEVICE_TYPES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="device_tokens")
    token = models.CharField(max_length=255)
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPES)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'token')
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    reminder = models.ForeignKey(Reminder, on_delete=models.CASCADE, related_name="notifications")
    subtask = models.ForeignKey(SubTask, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.CharField(max_length=500)
    scheduled_time = models.DateTimeField()
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_time}"
