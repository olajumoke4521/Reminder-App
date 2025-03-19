from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Tag(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tags")
    
    def __str__(self):
        return self.name
    
    
class Reminder(models.Model):
    
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
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
