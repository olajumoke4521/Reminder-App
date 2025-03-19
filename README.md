# Reminder Application Documentation 
 
## Table of Contents 
1. [System Overview](#system-overview) 
2. [Architecture](#architecture) 
3. [Data Models](#data-models) 
4. [API Endpoints](#api-endpoints) 
5. [Notification System](#notification-system) 
6. [Background Processing](#background-processing) 
7. [Client-Side Integration](#client-side-integration) 
8. [Key Process Flows](#key-process-flows) 
9. [Deployment and Configuration](#deployment-and-configuration) 
 
## System Overview 
 
The Reminder Application is a comprehensive task management system built with Django and Django REST Framework. It allows users to create, manage, and receive notifications for reminders and subtasks. The application features a robust notification system using Firebase Cloud Messaging for push notifications and email for email notifications. 
 
### Key Features 
 
- **Reminder Management**: Create, update, delete, and view reminders with various attributes 
- **Subtask Support**: Break down reminders into smaller subtasks 
- **Tagging System**: Organize reminders and subtasks with tags 
- **Recurring Reminders**: Set up reminders that repeat on various schedules 
- **Priority Levels**: Assign priority levels to reminders and subtasks 
- **Multi-channel Notifications**: Receive notifications via push notifications and/or email 
- **Early Reminders**: Get notified before the actual reminder time 
- **Device Management**: Register and manage multiple devices for push notifications 
 
## Architecture 
 
The application follows a standard Django architecture with REST API endpoints, enhanced with background processing capabilities through Celery and push notification support through Firebase. 
 
### Component Overview 
 
1. **Django Backend**: Core application logic, models, views, and API endpoints 
2. **Django REST Framework**: API layer for client communication 
3. **Celery**: Background task processing for notifications and recurring reminders 
4. **Redis**: Message broker for Celery tasks 
5. **Firebase Cloud Messaging**: Push notification delivery to web and mobile clients 
6. **PostgreSQL**: Database for storing application data 
 
 
## Data Models 
 
The application uses several interconnected models to represent reminders, subtasks, tags, notifications, and device tokens. 
 
### Core Models 
 
#### User 
The application uses Django's built-in User model for authentication and user management. 
 
#### Reminder 
The central model representing a reminder with the following key attributes: 
- Basic information: title, description, date, time 
- Configuration: is_all_day, early_reminder, repeat options 
- Status tracking: is_completed, completed_at, is_flagged, priority 
- Notification preferences: email, push, or both 
- Relationships: user (owner), tags, subtasks 
 
#### SubTask 
Represents a component of a reminder with similar attributes: 
- Basic information: title, description, date, time 
- Status tracking: is_completed, completed_at, is_flagged, priority 
- Relationships: reminder (parent), tags 
 
#### Tag 
Simple model for categorizing reminders and subtasks: 
- name: The tag name 
- user: The owner of the tag 
 
#### DeviceToken 
Stores information about user devices for push notifications: 
- token: The FCM token for the device 
- device_type: Type of device (iOS, Android, Web) 
- is_active: Whether the token is currently active 
- user: The owner of the device 
 
#### Notification 
Tracks notification status and delivery: 
- title, message: Content of the notification 
- scheduled_time: When the notification should be sent 
- sent, sent_at: Tracking of notification delivery 
- Relationships: user, reminder, subtask (optional) 
 
## API Endpoints 
 
The application provides a comprehensive REST API for client interaction. 
 
### Authentication 
 
- `POST /api/auth/token/`: Obtain an authentication token 
 
### Reminders 
 
- `GET /api/reminders/`: List all reminders 
- `POST /api/reminders/`: Create a new reminder 
- `GET /api/reminders/{id}/`: Retrieve a specific reminder 
- `PUT /api/reminders/{id}/`: Update a specific reminder 
- `DELETE /api/reminders/{id}/`: Delete a specific reminder 
- `POST /api/reminders/{id}/complete/`: Mark a reminder as complete 
- `POST /api/reminders/{id}/uncomplete/`: Mark a reminder as incomplete 
- `POST /api/reminders/{id}/toggle_flag/`: Toggle the flagged status 
- `GET /api/reminders/upcoming/`: List upcoming reminders 
- `GET /api/reminders/scheduled/`: List scheduled reminders 
- `GET /api/reminders/flagged/`: List flagged reminders 
- `GET /api/reminders/stats/`: Get reminder statistics 
- `GET /api/reminders/{id}/subtasks/`: List subtasks for a reminder 
- `POST /api/reminders/{id}/add_subtask/`: Add a subtask to a reminder 
- `GET /api/reminders/{reminder_id}/subtasks/{subtask_id}/`: Get a specific subtask within a reminder 
- `PUT /api/reminders/{reminder_id}/subtasks/{subtask_id}/`: Update a specific subtask within a reminder 
- `DELETE /api/reminders/{reminder_id}/subtasks/{subtask_id}/`: Delete a specific subtask within a reminder 
- `POST /api/reminders/{reminder_id}/subtasks/{subtask_id}/complete/`: Mark a specific subtask as complete 
- `POST /api/reminders/{reminder_id}/subtasks/{subtask_id}/uncomplete/`: Mark a specific subtask as incomplete 
- `POST /api/reminders/{reminder_id}/subtasks/{subtask_id}/toggle_flag/`: Toggle the flagged status of a specific subtask 
 
### Subtasks 
 
- `GET /api/subtasks/`: List all subtasks 
- `POST /api/subtasks/`: Create a new subtask 
- `GET /api/subtasks/{id}/`: Retrieve a specific subtask 
- `PUT /api/subtasks/{id}/`: Update a specific subtask 
- `DELETE /api/subtasks/{id}/`: Delete a specific subtask 
- `POST /api/subtasks/{id}/complete/`: Mark a subtask as complete 
- `POST /api/subtasks/{id}/uncomplete/`: Mark a subtask as incomplete 
- `POST /api/subtasks/{id}/toggle_flag/`: Toggle the flagged status 

 
### Tags 
 
- `GET /api/tags/`: List all tags 
- `POST /api/tags/`: Create a new tag 
- `GET /api/tags/{id}/`: Retrieve a specific tag 
- `PUT /api/tags/{id}/`: Update a specific tag 
- `DELETE /api/tags/{id}/`: Delete a specific tag 
- `GET /api/tags/with_counts/`: List tags with counts of associated reminders and subtasks 
- `GET /api/tags/{id}/reminders/`: List reminders associated with a tag 
- `GET /api/tags/{id}/subtasks/`: List subtasks associated with a tag 
 
### Device Tokens 
 
- `GET /api/device-tokens/`: List all device tokens 
- `POST /api/device-tokens/`: Register a new device token 
- `GET /api/device-tokens/{id}/`: Retrieve a specific device token 
- `PUT /api/device-tokens/{id}/`: Update a specific device token 
- `DELETE /api/device-tokens/{id}/`: Delete a specific device token 
- `POST /api/device-tokens/{id}/deactivate/`: Deactivate a device token 
 
### Notifications 
 
- `GET /api/notifications/`: List all notifications 
- `GET /api/notifications/{id}/`: Retrieve a specific notification 
 
### Testing 
 
- `GET /notifications/test/`: View the notification testing page 
- `POST /api/test-notification/`: Send a test notification 
 
## Notification System 
 
The notification system is a core component of the application, responsible for scheduling, managing, and delivering notifications to users. 
 
### Components 
 
1. **NotificationService**: Central service for notification management 
2. **Firebase Cloud Messaging**: Delivers push notifications to web and mobile clients 
3. **Email Backend**: Sends email notifications 
4. **Celery Tasks**: Processes notifications in the background 
 
### Notification Flow 
 
1. **Scheduling**: 
   - When a reminder or subtask is created or updated, the system schedules notifications based on the date, time, and early reminder settings. 
   - For recurring reminders, the system schedules future instances based on the repeat pattern. 
 
2. **Processing**: 
   - A Celery task runs every minute to check for due notifications. 
   - When a notification is due, the system attempts to deliver it via the user's preferred channels (email, push, or both). 
 
3. **Delivery**: 
   - For push notifications, the system sends the notification to all active devices registered for the user. 
   - For email notifications, the system sends an HTML email with the reminder details. 
 
4. **Tracking**: 
   - The system tracks the delivery status of notifications, marking them as sent when delivered successfully. 
   - Old notifications are automatically cleaned up after a configurable period (default 30 days). 
 

## Background Processing 
 
The application uses Celery for background task processing, with Redis as the message broker. 
 
### Key Tasks 
 
1. **send_due_notifications**: Runs every minute to check for and send due notifications. 
2. **reschedule_recurring_reminders**: Runs daily to schedule future instances of recurring reminders. 
3. **check_overdue_items**: Runs daily to check for overdue reminders and subtasks and send notifications. 
4. **clean_old_notifications**: Runs weekly to remove old sent notifications. 
 
### Task Scheduling 
 
The Celery Beat scheduler is configured in settings.py with the following schedule: 
 
```python 
CELERY_BEAT_SCHEDULE = { 
    'send-due-notifications': { 
        'task': 'reminders.tasks.send_due_notifications', 
        'schedule': 60.0,  # Every minute 
    }, 
    'reschedule-recurring-reminders': { 
        'task': 'reminders.tasks.reschedule_recurring_reminders', 
        'schedule': 3600.0 * 24,  # Daily 
    }, 
    'clean-old-notifications': { 
        'task': 'reminders.tasks.clean_old_notifications', 
        'schedule': 3600.0 * 24 * 7,  # Weekly 
    }, 
    'check-overdue-items': { 
        'task': 'reminders.tasks.check_overdue_items', 
        'schedule': 3600.0 * 24,  # Daily 
    }, 
} 
``` 
 
## Client-Side Integration 
 
The application provides client-side integration for web applications through Firebase Cloud Messaging. 
 
### Service Worker 
 
A Firebase messaging service worker (firebase-messaging-sw.js) handles push notifications on the client side: 
 
1. **Background Message Handling**: Displays notifications when the app is in the background 
2. **Notification Click Handling**: Opens the appropriate page when a notification is clicked 
3. **Service Worker Lifecycle**: Manages installation and activation of the service worker 
 
### Client Integration Steps 
 
1. **Register Service Worker**: The client registers the Firebase messaging service worker 
2. **Request Permission**: The client requests notification permission from the browser 
3. **Get FCM Token**: The client retrieves an FCM token from Firebase 
4. **Register Token with Server**: The client sends the FCM token to the server 
5. **Receive Notifications**: The client receives and displays notifications 
 
## Key Process Flows 
 
### Reminder Creation Flow 
 
1. Client sends a POST request to `/api/reminders/` with reminder details 
2. Server creates the reminder in the database 
3. `post_save` signal triggers the `reminder_saved` handler 
4. Handler calls `NotificationService.schedule_notifications_for_reminder` 
5. If it's a recurring reminder, `NotificationService.schedule_recurring_reminders` is called 
6. Notifications are created in the database with appropriate scheduled times 
7. Server returns the created reminder to the client 
 
### Notification Delivery Flow 
 
1. Celery task `send_due_notifications` runs every minute 
2. Task queries for unsent notifications that are due 
3. For each due notification: 
   - If email notification is enabled, send email 
   - If push notification is enabled, get active device tokens 
   - For each device token, send push notification via Firebase 
   - Mark notification as sent if delivered successfully 
 
### Recurring Reminder Flow 
 
1. User creates or updates a reminder with a repeat option 
2. `post_save` signal triggers the `reminder_saved` handler 
3. Handler calls `NotificationService.schedule_recurring_reminders` 
4. Service calculates future dates based on the repeat pattern 
5. For each future date within the scheduling window (default 90 days): 
   - Create a notification for that date 
6. Daily Celery task `reschedule_recurring_reminders` runs 
7. Task finds all active recurring reminders 
8. For each reminder, calls `NotificationService.schedule_recurring_reminders` 
9. Service schedules new notifications for dates that have come into the scheduling window 
 
## Deployment and Configuration 
 
### Requirements 
 
- Python 3.8+ 
- PostgreSQL 
- Redis 
- Firebase project with Cloud Messaging enabled 
 
### Configuration 
 
The application is configured through Django settings: 
 
1. **Database**: PostgreSQL connection details 
2. **Email**: SMTP server configuration for email notifications 
3. **Celery**: Redis connection details and task scheduling 
4. **Firebase**: Service account key path and web app configuration 
 
### Firebase Setup 
 
1. Create a Firebase project 
2. Enable Cloud Messaging 
3. Generate a service account key and save it as `firebase-service-account.json` 
4. Configure the web app settings in `settings.py` 
5. Generate a VAPID key for web push notifications 
 
### Running the Application 
 
1. Start the Django development server 
2. Start Celery worker: `celery -A reminder_app worker -l info` 
3. Start Celery beat: `celery -A reminder_app beat -l info` 
4. Ensure Redis is running for Celery message broker 