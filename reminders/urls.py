from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views


router = DefaultRouter()
router.register(r'reminders', views.ReminderViewSet, basename='reminder')
router.register(r'subtasks', views.SubTaskViewSet, basename='subtask')
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'device-tokens', views.DeviceTokenViewSet, basename='device-token')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    path('reminders/<int:reminder_id>/subtasks/<int:subtask_id>/', views.reminder_subtask_view),
    path('reminders/<int:reminder_id>/subtasks/<int:subtask_id>/complete/', views.reminder_subtask_complete),
    path('reminders/<int:reminder_id>/subtasks/<int:subtask_id>/uncomplete/', views.reminder_subtask_uncomplete),
    path('reminders/<int:reminder_id>/subtasks/<int:subtask_id>/toggle_flag/', views.reminder_subtask_toggle_flag),
]