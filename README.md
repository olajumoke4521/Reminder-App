# Reminder App

A comprehensive task management and reminder application with multi-channel notifications, recurring reminders, and subtask support.


## Features

- **Comprehensive Reminder Management**
  - Create, edit, and delete reminders with detailed information
  - Set dates, times, and optional all-day reminders
  - Add descriptions, locations, and priority levels
  - Flag important reminders for quick access

- **Subtask Support**
  - Break down reminders into manageable subtasks
  - Track completion status of individual subtasks
  - Set separate dates and priorities for subtasks

- **Multi-channel Notifications**
  - Receive notifications via email, push notifications, or both
  - Get early reminders before the scheduled time
  - Customize notification preferences per reminder

- **Recurring Reminders**
  - Set reminders to repeat on various schedules (daily, weekly, monthly, etc.)
  - Configure custom repeat patterns
  - Set end dates for recurring reminders

- **Tagging System**
  - Organize reminders and subtasks with tags
  - Filter and search by tags
  - View tag usage statistics

- **Cross-platform Support**
  - Web application with responsive design
  - Push notifications on desktop and mobile browsers
  - Support for multiple devices per user

![Reminder Details](./screenshots/reminder_details.png)
*Screenshot: Detailed view of a reminder with subtasks*

## Technology Stack

- **Backend**
  - Django & Django REST Framework
  - PostgreSQL database
  - Celery for background tasks
  - Redis for message broker
  - Firebase Cloud Messaging for push notifications

- **Frontend**
  - HTML, CSS, JavaScript
  - Responsive design
  - Service worker for push notifications

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- Firebase project with Cloud Messaging enabled

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/olajumoke4521/Reminder-App.git
   cd reminder-app
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file with your configuration:
   ```
   DATABASE=
   EMAIL_HOST=smtp.example.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email@example.com
   EMAIL_HOST_PASSWORD=your_email_password
   REDIS_URL=redis://localhost:6379/0
   ```

6. Set up Firebase:
   - Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
   - Enable Cloud Messaging
   - Generate a service account key and save it as `firebase-service-account.json` in the project root
   - Update Firebase settings in `settings.py` with your project details

7. Run migrations:
   ```bash
   python manage.py migrate
   ```

8. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

## Running the Application

1. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

2. Start Celery worker:
   ```bash
   celery -A reminder_app worker -l info --pool=solo
   ```

3. Start Celery beat for scheduled tasks:
   ```bash
   celery -A reminder_app beat -l info
   ```

4. Access the application at http://localhost:8000

## API Documentation

The application provides a comprehensive REST API for client integration.

### Authentication

- `POST /api/auth/token/`: Obtain an authentication token

### Reminders

- `GET /api/reminders/`: List all reminders
- `POST /api/reminders/`: Create a new reminder
- `GET /api/reminders/{id}/`: Retrieve a specific reminder
- `PUT /api/reminders/{id}/`: Update a specific reminder
- `DELETE /api/reminders/{id}/`: Delete a specific reminder
- `POST /api/reminders/{id}/complete/`: Mark a reminder as complete
- `GET /api/reminders/upcoming/`: List upcoming reminders
- `GET /api/reminders/stats/`: Get reminder statistics

### Subtasks

- `GET /api/subtasks/`: List all subtasks
- `POST /api/subtasks/`: Create a new subtask
- `GET /api/subtasks/{id}/`: Retrieve a specific subtask
- `POST /api/subtasks/{id}/complete/`: Mark a subtask as complete

### Tags

- `GET /api/tags/`: List all tags
- `POST /api/tags/`: Create a new tag
- `GET /api/tags/with_counts/`: List tags with counts of associated items

For complete API documentation, see the [API Documentation]


## Push Notification Setup

To enable push notifications in your browser:

1. Access the notification test page at `/notifications/test/`
2. Click "Register Service Worker"
3. Click "Enable Notifications" and allow when prompted
4. Your browser will register with Firebase and display the FCM token
5. Test notifications using the form at the bottom of the page


## Development

### Project Structure

```
reminder_app/
├── reminder_app/          # Main Django project
│   ├── settings.py        # Project settings
│   ├── urls.py            # Main URL configuration
│   └── celery.py          # Celery configuration
├── reminders/             # Reminders app
│   ├── models.py          # Data models
│   ├── views.py           # API views and controllers
│   ├── serializers.py     # REST serializers
│   ├── urls.py            # API URL patterns
│   ├── tasks.py           # Celery tasks
│   ├── signals.py         # Django signals
│   └── notification_service.py  # Notification logic
├── templates/             # HTML templates
└── static/                # Static files (CSS, JS, images)
```

### Key Components

- **Models**: Define the data structure for reminders, subtasks, tags, etc.
- **Views**: Handle API requests and responses
- **Serializers**: Transform data between Python objects and JSON
- **Tasks**: Background processing for notifications and recurring reminders
- **Signals**: Automatically trigger actions when models are saved/deleted
- **Notification Service**: Core logic for scheduling and sending notifications

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery](https://docs.celeryproject.org/)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)