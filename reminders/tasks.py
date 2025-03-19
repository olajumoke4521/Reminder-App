from celery import shared_task
from django.db.models import Q
from django.utils import timezone
from .models import Reminder, Notification, SubTask
from .notification_service import NotificationService


@shared_task
def send_due_notifications():
    """Celery task to send notifications that are due"""
    NotificationService.send_due_notifications()


@shared_task
def reschedule_recurring_reminders(days_ahead=90):
    """Celery task to schedule upcoming recurring reminders"""
    reminders = Reminder.objects.filter(
        ~Q(repeat='never'), 
        is_completed=False
    )
    
    for reminder in reminders:
        NotificationService.schedule_recurring_reminders(reminder, days_ahead)

@shared_task
def check_overdue_items():
    """Check for overdue reminders and subtasks and send notifications"""
    today = timezone.now().date()
    
    overdue_reminders = Reminder.objects.filter(
        date__lt=today,
        is_completed=False
    )
    
    for reminder in overdue_reminders:
        if not Notification.objects.filter(
            reminder=reminder,
            subtask=None,  
            title__startswith="Overdue",
            sent_at__date=today  
        ).exists():
            # Calculate days overdue
            days_overdue = (today - reminder.date).days
            overdue_text = "yesterday" if days_overdue == 1 else f"{days_overdue} days ago"
            
            Notification.objects.create(
                user=reminder.user,
                reminder=reminder,
                subtask=None,
                title=f"Overdue: {reminder.title}",
                message=f"This reminder was due {overdue_text}",
                scheduled_time=timezone.now(),
                sent=False
            )
    
    overdue_subtasks = SubTask.objects.filter(
        date__lt=today,
        is_completed=False
    )
    
    for subtask in overdue_subtasks:
        if not Notification.objects.filter(
            reminder=subtask.reminder,
            subtask=subtask,
            title__startswith="Overdue",
            sent_at__date=today  
        ).exists():
            # Calculate days overdue
            days_overdue = (today - subtask.date).days
            overdue_text = "yesterday" if days_overdue == 1 else f"{days_overdue} days ago"
            
            Notification.objects.create(
                user=subtask.reminder.user,
                reminder=subtask.reminder,
                subtask=subtask,
                title=f"Overdue: {subtask.title}",
                message=f"This subtask was due {overdue_text}",
                scheduled_time=timezone.now(),
                sent=False
            )

@shared_task
def clean_old_notifications(days=30):
    """Celery task to remove old sent notifications"""
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    Notification.objects.filter(
        sent=True,
        sent_at__lt=cutoff_date
    ).delete()
