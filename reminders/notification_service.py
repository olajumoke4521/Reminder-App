from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from firebase_admin import messaging
from .models import Reminder, Notification, DeviceToken

class NotificationService:
    @staticmethod
    def schedule_notifications_for_reminder(reminder):
        """Schedule notifications for a reminder based on its early reminder setting"""
        Notification.objects.filter(reminder=reminder).delete()
        
        # If no date/time or reminder is completed, don't schedule
        if not reminder.date or reminder.is_completed:
            return
        
        # Calculate notification time based on reminder settings
        reminder_datetime = None
        
        if reminder.time:
            # Combine date and time
            reminder_datetime = timezone.make_aware(
                timezone.datetime.combine(reminder.date, reminder.time)
            )
        else:
            # All-day reminder, default to 9:00 AM
            reminder_datetime = timezone.make_aware(
                timezone.datetime.combine(reminder.date, timezone.datetime.min.time().replace(hour=9))
            )
        
        # Schedule the main notification
        Notification.objects.create(
            user=reminder.user,
            reminder=reminder,
            title=reminder.title,
            message=reminder.description or "Time for your reminder!",
            scheduled_time=reminder_datetime
        )
        
        # Schedule early reminder if set
        if reminder.early_reminder != 'none':
            early_time = None
            
            if reminder.early_reminder == 'custom' and reminder.custom_early_reminder:
                early_time = reminder_datetime - reminder.custom_early_reminder
            else:
                delta_mapping = {
                    '5min': timedelta(minutes=5),
                    '10min': timedelta(minutes=15),
                }
                
                if reminder.early_reminder in delta_mapping:
                    early_time = reminder_datetime - delta_mapping[reminder.early_reminder]
            
            if early_time:
                Notification.objects.create(
                    user=reminder.user,
                    reminder=reminder,
                    title=f"Upcoming: {reminder.title}",
                    message=f"Reminder coming up {reminder.get_early_reminder_display()}",
                    scheduled_time=early_time
                )
    
    @staticmethod
    def schedule_recurring_reminders(reminder, future_days=90):
        """Schedule future instances of recurring reminders"""
        if reminder.repeat == 'never' or not reminder.date:
            return []
        
        end_date = reminder.repeat_end_date or (timezone.now().date() + timedelta(days=future_days))
        
        if reminder.repeat_end_date and reminder.date > reminder.repeat_end_date:
            return []
        
        # Calculate next dates based on repeat pattern
        next_dates = []
        current_date = reminder.date
        
        while current_date <= end_date:
            # Add the next date based on repeat type
            if reminder.repeat == 'daily':
                current_date += timedelta(days=1)
            elif reminder.repeat == 'weekdays':
                current_date += timedelta(days=1)
                # Skip weekends
                while current_date.weekday() >= 5:  
                    current_date += timedelta(days=1)
            elif reminder.repeat == 'weekends':
                current_date += timedelta(days=1)
                # Skip weekdays
                while current_date.weekday() < 5: 
                    current_date += timedelta(days=1)
            elif reminder.repeat == 'weekly':
                current_date += timedelta(weeks=1)
            elif reminder.repeat == 'biweekly':
                current_date += timedelta(weeks=2)
            elif reminder.repeat == 'monthly':
                month = current_date.month + 1
                year = current_date.year
                if month > 12:
                    month = 1
                    year += 1
                
                # Handle month length differences
                day = min(current_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
                current_date = current_date.replace(year=year, month=month, day=day)
            elif reminder.repeat == 'quarterly':
                # Move 3 months ahead
                month = current_date.month + 3
                year = current_date.year
                while month > 12:
                    month -= 12
                    year += 1
                
                # Handle month length differences
                day = min(current_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
                current_date = current_date.replace(year=year, month=month, day=day)
            elif reminder.repeat == 'biannually':
                # Move 6 months ahead
                month = current_date.month + 6
                year = current_date.year
                if month > 12:
                    month -= 12
                    year += 1
                
                # Handle month length differences
                day = min(current_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
                current_date = current_date.replace(year=year, month=month, day=day)
            elif reminder.repeat == 'yearly':
                current_date = current_date.replace(year=current_date.year + 1)
            elif reminder.repeat == 'hourly':
                # For hourly, we'll add notifications within the same day
                if reminder.time:
                    # Add only the first few hourly reminders to avoid creating too many
                    reminder_datetime = timezone.make_aware(
                        timezone.datetime.combine(current_date, reminder.time)
                    )
                    for i in range(1, min(24, future_days)):
                        next_datetime = reminder_datetime + timedelta(hours=i)
                        # Only add if it's on the same day
                        if next_datetime.date() == current_date:
                            Notification.objects.create(
                                user=reminder.user,
                                reminder=reminder,
                                title=reminder.title,
                                message=reminder.description or "Time for your reminder!",
                                scheduled_time=next_datetime
                            )
                # Move to next day for the hourly pattern
                current_date += timedelta(days=1)
                continue
            elif reminder.repeat == 'custom' and reminder.custom_repeat_interval:
                # Handle custom repeat patterns
                interval = reminder.custom_repeat_interval
                
                if 'days' in interval:
                    current_date += timedelta(days=interval['days'])
                elif 'weeks' in interval:
                    current_date += timedelta(weeks=interval['weeks'])
                elif 'months' in interval:
                    # Move X months ahead
                    month = current_date.month + interval['months']
                    year = current_date.year
                    while month > 12:
                        month -= 12
                        year += 1
                    
                    # Handle month length differences
                    day = min(current_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
                    current_date = current_date.replace(year=year, month=month, day=day)
                else:
                    # Default to daily if custom pattern is invalid
                    current_date += timedelta(days=1)
            else:
                # Default for any unhandled repeat types
                break
            
            # Add to list of next dates if within the end date
            if current_date <= end_date:
                next_dates.append(current_date)
        
        return next_dates
    
    @staticmethod
    def schedule_notifications_for_subtask(subtask):
        """Schedule notifications for a subtask based on its date/time"""
        Notification.objects.filter(subtask=subtask).delete()
        
        # If no date/time or subtask is completed, don't schedule
        if not subtask.date or subtask.is_completed:
            return
        
        # Calculate notification time based on subtask settings
        subtask_datetime = None
        
        if subtask.time:
            subtask_datetime = timezone.make_aware(
                timezone.datetime.combine(subtask.date, subtask.time)
            )
        else:
            # All-day subtask, default to 9:00 AM
            subtask_datetime = timezone.make_aware(
                timezone.datetime.combine(subtask.date, timezone.datetime.min.time().replace(hour=9))
            )
        
        # Schedule the main notification
        Notification.objects.create(
            user=subtask.reminder.user,
            reminder=subtask.reminder,
            subtask=subtask,
            title=f"Subtask: {subtask.title}",
            message=subtask.description or "Time for your subtask!",
            scheduled_time=subtask_datetime
        )

    @staticmethod
    def send_due_notifications():
        """Send notifications that are due now"""
        now = timezone.now()
        
        # Get all unsent notifications that are due
        due_notifications = Notification.objects.filter(
            sent=False,
            scheduled_time__lte=now
        ).select_related('user', 'reminder', 'subtask')
        
        for notification in due_notifications:
            reminder = notification.reminder
            user = notification.user
            subtask = notification.subtask
            notification_preference = reminder.notification_preference
            sent_successfully = False
            
            item = subtask if subtask else reminder
            item_id = subtask.id if subtask else reminder.id 
            item_type = "subtask" if subtask else "reminder"

            # Handle email notifications
            if notification_preference in ['email', 'both']:
                email_sent = NotificationService.send_email_notification(
                    user.email,
                    notification.title,
                    notification.message,
                    item,
                    item_type
                )
                if email_sent:
                    sent_successfully = True
            
            # Handle push notifications
            if notification_preference in ['push', 'both']:
                # Get active device tokens for this user
                device_tokens = DeviceToken.objects.filter(
                    user=user,
                    is_active=True
                )
                
                # Send to each device
                for device in device_tokens:
                    if device.device_type == 'web':
                        sent = NotificationService.send_web_notification(
                            device.token,
                            notification.title,
                            notification.message,
                            reminder.id,
                            subtask.id if subtask else None,
                            item_type
                        )
                    else:
                        sent = False
                    
                    if sent:
                        sent_successfully = True
            
            # Mark notification as sent if either email or push notification was sent successfully
            if sent_successfully:
                notification.sent = True
                notification.sent_at = now
                notification.save()
            
            # If no devices and no email (or delivery failed), mark as sent anyway to avoid repeated attempts
            if not sent_successfully:
                notification.sent = True
                notification.sent_at = now
                notification.save()

    @staticmethod
    def send_web_notification(token, title, message, reminder_id, subtask_id=None, item_type='None'):
        """Send web push notification using Firebase Admin SDK"""
        try:
            # Create message payload
            notification = messaging.Notification(
                title=title,
                body=message,
            )
            
            data = {
                'reminder_id': str(reminder_id),
                'item_type': item_type
            }
            
            # Add subtask_id if provided
            if subtask_id:
                data['subtask_id'] = str(subtask_id)
                data['click_action'] = f'/reminders/{reminder_id}/subtasks/{subtask_id}/'
            else:
                data['click_action'] = f'/reminders/{reminder_id}/'
                
            # Create and send message
            message = messaging.Message(
                notification=notification,
                data=data,
                token=token,
                webpush=messaging.WebpushConfig(
                    headers={
                        'TTL': '86400'  
                    },
                    notification=messaging.WebpushNotification(
                        icon='/static/reminders/images/notification-icon.png'
                    )
                )
            )
            
            # Send the message
            response = messaging.send(message)
            print(f'Successfully sent message: {response}')
            return True
        except Exception as e:
            print(f'Error sending message: {e}')
            return False
        
    @staticmethod
    def send_notification_to_user(user, title, message, reminder_id, subtask_id=None, item_type='reminder'):
        """Send notification to all active devices for a user"""
        
        # Get all active device tokens for the user
        device_tokens = DeviceToken.objects.filter(
            user=user,
            is_active=True
        )
        
        if not device_tokens.exists():
            return False
     
        success = False
        
        # Send to each device
        for device in device_tokens:
            if device.device_type == 'web':
                sent = NotificationService.send_web_notification(
                    device.token, title, message, reminder_id, subtask_id, item_type
                )
                success = success or sent
        
        return success
            
    @staticmethod
    def send_email_notification(email, title, message, item, item_type):
        """Send email notification to the user"""
        try:
            if not email:
                return False
           
            subject = f"Reminder: {title}"
            
            date_str = item.date.strftime('%A, %B %d, %Y') if item.date else None
            time_str = item.time.strftime('%I:%M %p') if hasattr(item, 'time') and item.time else None
            
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ padding: 20px; }}
                    .reminder {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>{title}</h1>
                    
                    <div class="reminder">
                        <p><strong>Type:</strong> {item_type.capitalize()}</p>
                        <p>{message}</p>
                        
                        {f'<p><strong>Date:</strong> {date_str}</p>' if date_str else ''}
                        {f'<p><strong>Time:</strong> {time_str}</p>' if time_str else ''}
                    </div>
                    
                    <p style="margin-top: 20px;">
                        This is a reminder from Reminder App.
                    </p>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            {title}

            Type: {item_type.capitalize()}
            
            {message}
            
            When: {date_str or 'No date'} {time_str or ''}
            
            Open the app to view more details.
            """
    
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False
            )
            
            print(f"Email notification sent to {email}: {title}")
            return True
        except Exception as e:
            print(f"Failed to send email notification: {e}")
            return False