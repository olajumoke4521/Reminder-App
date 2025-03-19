import firebase_admin
from firebase_admin import credentials
from django.conf import settings

def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized"""
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(settings.FIREBASE_SETTINGS['SERVICE_ACCOUNT_KEY_PATH'])
        firebase_admin.initialize_app(cred)