from rest_framework import viewsets, filters, status, serializers
from rest_framework.decorators import action,  api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from .models import (
    Reminder, SubTask, Tag, DeviceToken, Notification
)
from .serializers import (
    ReminderSerializer, SubTaskSerializer, TagSerializer,
    DeviceTokenSerializer, NotificationSerializer, SubTaskCreateSerializer
)
from django.http import HttpResponse
from django.template import Template, Context
from django.conf import settings
from django.db import models
import os
from django.shortcuts import render
from firebase_admin import messaging
import time
import traceback

class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def with_counts(self, request):
        """Return all tags with counts of associated reminders and subtasks"""
        tags = self.get_queryset()
        
        result = []
        for tag in tags:
            result.append({
                'id': tag.id,
                'name': tag.name,
                'reminder_count': tag.reminders.count(),
                'subtask_count': tag.subtasks.count(),
                'total_usage': tag.reminders.count() + tag.subtasks.count()
            })
        
        # Sort by total usage by default
        result = sorted(result, key=lambda x: x['total_usage'], reverse=True)
        
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def reminders(self, request, pk=None):
        """Return all reminders associated with this tag"""
        tag = self.get_object()
        reminders = tag.reminders.filter(user=request.user)
        
        page = self.paginate_queryset(reminders)
        if page is not None:
            serializer = ReminderSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ReminderSerializer(reminders, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def subtasks(self, request, pk=None):
        """Return all subtasks associated with this tag"""
        tag = self.get_object()
        subtasks = tag.subtasks.filter(reminder__user=request.user)
        
        page = self.paginate_queryset(subtasks)
        if page is not None:
            serializer = SubTaskSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = SubTaskSerializer(subtasks, many=True, context={'request': request})
        return Response(serializer.data)
    

class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_completed', 'is_flagged', 'priority', 'tags']
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'time', 'created_at', 'priority', 'title']
    
    def get_queryset(self):
        queryset = Reminder.objects.filter(user=self.request.user)
        
        # Filter by specific date
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        # Filter today's reminders
        today = self.request.query_params.get('today')
        if today and today.lower() == 'true':
            today_date = timezone.now().date()
            queryset = queryset.filter(date=today_date)
        
        # Filter reminders with no date (anytime)
        anytime = self.request.query_params.get('anytime')
        if anytime and anytime.lower() == 'true':
            queryset = queryset.filter(date__isnull=True)
        
        # Filter by tag name
        tag_name = self.request.query_params.get('tag_name')
        if tag_name:
            queryset = queryset.filter(tags__name=tag_name)

        # Filter by multiple tags (require all tags)
        tag_ids = self.request.query_params.get('tag_ids')
        if tag_ids:
            tag_id_list = tag_ids.split(',')
            for tag_id in tag_id_list:
                queryset = queryset.filter(tags__id=tag_id)
        
        # Default ordering if not specified
        ordering = self.request.query_params.get('ordering')
        if not ordering:
            queryset = queryset.order_by('date', 'time')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        reminder = self.get_object()
        reminder.mark_as_completed()
        return Response({'status': 'reminder marked as completed'})
    
    @action(detail=True, methods=['post'])
    def uncomplete(self, request, pk=None):
        reminder = self.get_object()
        reminder.is_completed = False
        reminder.completed_at = None
        reminder.save()
        return Response({'status': 'reminder marked as uncompleted'})
    
    @action(detail=True, methods=['post'])
    def toggle_flag(self, request, pk=None):
        reminder = self.get_object()
        reminder.is_flagged = not reminder.is_flagged
        reminder.save()
        return Response({'status': 'flag toggled', 'is_flagged': reminder.is_flagged})
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            Q(is_completed=False) & 
            Q(date__gte=today)
        ).order_by('date', 'time')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def scheduled(self, request):
        queryset = self.get_queryset().filter(
            Q(is_completed=False) & 
            Q(date__isnull=False)
        ).order_by('date', 'time')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def flagged(self, request):
        queryset = self.get_queryset().filter(is_flagged=True)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Return counts of reminders by different statuses"""
        user_reminders = Reminder.objects.filter(user=request.user)
        
        today = timezone.now().date()
        
        stats = {
            'total': user_reminders.count(),
            'completed': user_reminders.filter(is_completed=True).count(),
            'flagged': user_reminders.filter(is_flagged=True).count(),
            'scheduled': user_reminders.filter(date__isnull=False).count(),
            'today': user_reminders.filter(date=today).count(),
            'overdue': user_reminders.filter(
                is_completed=False,
                date__lt=today
            ).count(),
            'high_priority': user_reminders.filter(priority='high').count(),
            'medium_priority': user_reminders.filter(priority='medium').count(),
            'low_priority': user_reminders.filter(priority='low').count(),
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def subtasks(self, request, pk=None):
        """Get all subtasks for a specific reminder"""
        reminder = self.get_object()
        subtasks = reminder.subtasks.all().order_by('order')
        
        page = self.paginate_queryset(subtasks)
        if page is not None:
            serializer = SubTaskSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = SubTaskSerializer(subtasks, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_subtask(self, request, pk=None):
        """Add a subtask to this reminder"""
        reminder = self.get_object()
        
        context = {'request': request}
        serializer = SubTaskCreateSerializer(data=request.data, context=context)
        
        if serializer.is_valid():
            serializer.validated_data['reminder'] = reminder
            
            # Get the highest order value and increment
            highest_order = reminder.subtasks.aggregate(models.Max('order'))['order__max'] or 0
            serializer.validated_data['order'] = highest_order + 1

            new_tag_names = serializer.validated_data.pop('new_tags', [])
            tags = serializer.validated_data.get('tags', [])
            
            subtask = serializer.save()

            if new_tag_names:
                for tag_name in new_tag_names:
                    tag, created = Tag.objects.get_or_create(
                        user=request.user,
                        name=tag_name
                    )
                    tags.append(tag)
        
            if tags:
                subtask.tags.set(tags)
            
            return Response(
                SubTaskSerializer(subtask, context=context).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def reminder_subtask_view(request, reminder_id, subtask_id):
    """Handle CRUD operations for a specific subtask within a reminder"""
    try:
        reminder = Reminder.objects.get(id=reminder_id, user=request.user)
        subtask = SubTask.objects.get(id=subtask_id, reminder=reminder)
    except (Reminder.DoesNotExist, SubTask.DoesNotExist):
        return Response({"detail": "Not found."}, status=404)

    # Handle different HTTP methods
    if request.method == 'GET':
        serializer = SubTaskSerializer(subtask)
        return Response(serializer.data)
        
    elif request.method in ['PUT', 'PATCH']:
        serializer = SubTaskCreateSerializer(
            subtask, 
            data=request.data, 
            partial=request.method=='PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(SubTaskSerializer(subtask).data)
        return Response(serializer.errors, status=400)
        
    elif request.method == 'DELETE':
        subtask.delete()
        return Response(status=204)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reminder_subtask_complete(request, reminder_id, subtask_id):
    """Mark a subtask as complete"""
    try:
        reminder = Reminder.objects.get(id=reminder_id, user=request.user)
        subtask = SubTask.objects.get(id=subtask_id, reminder=reminder)
    except (Reminder.DoesNotExist, SubTask.DoesNotExist):
        return Response({"detail": "Not found."}, status=404)
        
    subtask.mark_as_completed()
    return Response({"status": "subtask marked as completed"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reminder_subtask_uncomplete(request, reminder_id, subtask_id):
    """Mark a subtask as incomplete"""
    try:
        reminder = Reminder.objects.get(id=reminder_id, user=request.user)
        subtask = SubTask.objects.get(id=subtask_id, reminder=reminder)
    except (Reminder.DoesNotExist, SubTask.DoesNotExist):
        return Response({"detail": "Not found."}, status=404)
        
    subtask.is_completed = False
    subtask.completed_at = None
    subtask.save()
    return Response({"status": "subtask marked as uncompleted"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reminder_subtask_toggle_flag(request, reminder_id, subtask_id):
    """Toggle flag on a subtask"""
    try:
        reminder = Reminder.objects.get(id=reminder_id, user=request.user)
        subtask = SubTask.objects.get(id=subtask_id, reminder=reminder)
    except (Reminder.DoesNotExist, SubTask.DoesNotExist):
        return Response({"detail": "Not found."}, status=404)
        
    subtask.is_flagged = not subtask.is_flagged
    subtask.save()
    return Response({"status": "flag toggled", "is_flagged": subtask.is_flagged})

class SubTaskViewSet(viewsets.ModelViewSet):
    serializer_class = SubTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['reminder', 'is_completed', 'is_flagged', 'priority', 'tags']
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'time', 'created_at', 'priority', 'order', 'title']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SubTaskCreateSerializer
        return SubTaskSerializer
    
    def get_queryset(self):
        queryset = SubTask.objects.filter(
            reminder__user=self.request.user
        )
        
        # Filter by specific date
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        # Filter today's subtasks
        today = self.request.query_params.get('today')
        if today and today.lower() == 'true':
            today_date = timezone.now().date()
            queryset = queryset.filter(date=today_date)
        
        # Filter by tag name
        tag_name = self.request.query_params.get('tag_name')
        if tag_name:
            queryset = queryset.filter(tags__name=tag_name)
            
        # Order by default
        ordering = self.request.query_params.get('ordering')
        if not ordering:
            queryset = queryset.order_by('order')
            
        return queryset
    
    
    def perform_create(self, serializer):
        reminder_id = serializer.validated_data.get('reminder').id
        reminder = Reminder.objects.get(id=reminder_id)
        
        # Check if reminder belongs to the authenticated user
        if reminder.user != self.request.user:
            raise serializers.ValidationError("You do not have permission to add subtasks to this reminder")
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        subtask = self.get_object()
        subtask.mark_as_completed()
        return Response({'status': 'subtask marked as completed'})
    
    @action(detail=True, methods=['post'])
    def uncomplete(self, request, pk=None):
        subtask = self.get_object()
        subtask.is_completed = False
        subtask.completed_at = None
        subtask.save()
        return Response({'status': 'subtask marked as uncompleted'})
    
    @action(detail=True, methods=['post'])
    def toggle_flag(self, request, pk=None):
        subtask = self.get_object()
        subtask.is_flagged = not subtask.is_flagged
        subtask.save()
        return Response({'status': 'flag toggled', 'is_flagged': subtask.is_flagged})

class DeviceTokenViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceTokenSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        device_token = self.get_object()
        device_token.is_active = False
        device_token.save()
        return Response({'status': 'device token deactivated'})


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-scheduled_time')

def firebase_messaging_sw(request):
    with open(os.path.join(settings.BASE_DIR, 'reminders/templates/firebase-messaging-sw.js'), 'r') as f:
        template_content = f.read()
    
    context = Context({
        'config': settings.FIREBASE_SETTINGS['WEB_APP_CONFIG']
    })
    
    template = Template(template_content)
    rendered_content = template.render(context)
  
    response = HttpResponse(rendered_content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response

def notification_test_page(request):
    """View for testing push notifications."""
    context = {
        'firebase_config': settings.FIREBASE_SETTINGS['WEB_APP_CONFIG'],
        'vapid_key': settings.FIREBASE_SETTINGS.get('VAPID_KEY', '')
    }
    return render(request, 'reminders/notification_test.html', context)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_notification(request):
    """API endpoint to send a test notification."""
    try:
        title = request.data.get('title', 'Test Notification')
        message = request.data.get('message', 'This is a test notification')
        token = request.data.get('token')
        
        # Validate token
        if not token:
            return Response({
                'status': False,
                'error': 'No FCM token provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create notification message
        notification = messaging.Notification(
            title=title,
            body=message,
        )
        
        webpush_config = messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                icon='/static/reminders/images/notification-icon.png',
            ),
        )
        
        # Create and send message
        message_obj = messaging.Message(
            notification=notification,
            data={
                'test': 'true',
                'timestamp': str(int(time.time())),
            },
            token=token,
            webpush=webpush_config
        )
        
        # Send the message
        response = messaging.send(message_obj)
        
        return Response({
            'status': True,
            'message': 'Notification sent successfully',
            'firebase_message_id': response
        })
    
    except Exception as e:
        error_message = str(e)
        print(f'Error sending test notification: {error_message}')
        traceback.print_exc()
        
        return Response({
            'status': False,
            'error': f'Error sending notification: {error_message}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)