"""
URL configuration for reminder_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from reminders import views
from reminders.views import firebase_messaging_sw
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('reminders.urls')),
    path('firebase-messaging-sw.js', firebase_messaging_sw, name='firebase-messaging-sw.js'),
    path('notifications/test/', views.notification_test_page, name='notification-test'),
    path('api/test-notification/', views.test_notification, name='test-notification'),
    path('accounts/', include('django.contrib.auth.urls')),  # Built-in auth views

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   