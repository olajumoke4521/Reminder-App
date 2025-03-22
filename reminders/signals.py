from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Reminder, SubTask, UserProfile
from .notification_service import NotificationService
from django.contrib.auth.models import User


@receiver(post_save, sender=Reminder)
def reminder_saved(sender, instance, created, **kwargs):
    """Signal handler for reminder saves to schedule notifications"""
    # Schedule notifications for the reminder
    NotificationService.schedule_notifications_for_reminder(instance)
    
    # If it's a recurring reminder, schedule future instances
    if not created and instance.repeat != 'never':
        NotificationService.schedule_recurring_reminders(instance)


@receiver(post_delete, sender=Reminder)
def reminder_deleted(sender, instance, **kwargs):
    """Signal handler for reminder deletion to clean up notifications"""
    # Delete all notifications for this reminder
    from .models import Notification
    Notification.objects.filter(reminder=instance).delete()

@receiver(post_save, sender=SubTask)
def subtask_saved(sender, instance, created, **kwargs):
    """Signal handler for subtask saves to schedule notifications"""
    # Schedule notifications for the subtask
    NotificationService.schedule_notifications_for_subtask(instance)

@receiver(post_delete, sender=SubTask)
def subtask_deleted(sender, instance, **kwargs):
    """Signal handler for subtask deletion to clean up notifications"""
    # Delete all notifications for this subtask
    from .models import Notification
    Notification.objects.filter(subtask=instance).delete()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile for each new User."""
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved."""
    UserProfile.objects.get_or_create(user=instance)