from django.apps import AppConfig


class RemindersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reminders'

    def ready(self):
        from .firebase_init import initialize_firebase
        initialize_firebase()
        
        import reminders.signals                                            