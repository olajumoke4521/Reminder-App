from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class TimezoneMiddleware(MiddlewareMixin):
    """Middleware to set timezone based on user preferences"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Try to get timezone from user profile or settings
            try:
                from django.contrib.auth.models import User
                user_timezone = request.user.profile.timezone
                if user_timezone:
                    timezone.activate(user_timezone)
                    return
            except (AttributeError, User.profile.RelatedObjectDoesNotExist):
                pass
        
        # Default to UTC if no user timezone is set
        timezone.activate('UTC')