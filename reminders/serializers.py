from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Reminder, SubTask, Tag, DeviceToken, Notification


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class SubTaskCreateSerializer(serializers.ModelSerializer): 
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        write_only=True,
        many=True,
        required=False,
        source='tags')
    
    new_tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )

    class Meta:
        model = SubTask
        fields = [
            'id', 'title', 'description', 'date', 'time', 'is_all_day',
            'is_completed', 'completed_at', 'is_flagged', 'priority',
            'reminder', 'tags', 'tag_ids', 'new_tags', 'order']
        read_only_fields = ['id']
        extra_kwargs = {
            'reminder': {'required': False}  
        }

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        new_tag_names = validated_data.pop('new_tags', [])
        
        subtask = SubTask.objects.create(**validated_data)
        
        if new_tag_names:
            user = subtask.reminder.user
            for tag_name in new_tag_names:
                tag, created = Tag.objects.get_or_create(
                    user=user,
                    name=tag_name
                )
                tags.append(tag)

        if tags:
            subtask.tags.set(tags)
        
        return subtask
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        new_tag_names = validated_data.pop('new_tags', [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        if new_tag_names:
            user = instance.reminder.user
            new_tags = []
            for tag_name in new_tag_names:
                tag, created = Tag.objects.get_or_create(
                    user=user,
                    name=tag_name
                )
                new_tags.append(tag)
            
            # If tags were not provided but new_tags were, we add new tags to existing ones
            if tags is None and new_tags:
                current_tags = list(instance.tags.all())
                tags = current_tags + new_tags
            # If both tags and new_tags were provided, we combine them
            elif tags is not None and new_tags:
                tags = list(tags) + new_tags
        
        # Update tags if provided
        if tags is not None:
            instance.tags.set(tags)
        
        return instance

class SubTaskSerializer(serializers.ModelSerializer):
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        write_only=True,
        many=True,
        required=False,
        source='tags'
    )
    new_tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )

    class Meta:
        model = SubTask
        fields = [
            'id', 'title', 'description', 'date', 'time', 'is_all_day',
            'is_completed', 'completed_at', 'is_flagged', 'priority',
            'reminder', 'tags', 'tag_ids', 'new_tags',
              'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']

class ReminderSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        write_only=True,
        many=True,
        required=False,
        source='tags'
    )
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    subtasks = SubTaskSerializer(many=True, read_only=True)
    subtasks_data = SubTaskSerializer(many=True, required=False, write_only=True)
    
    class Meta:
        model = Reminder
        fields = [
            'id', 'title', 'description', 'date', 'time', 'is_all_day',
            'early_reminder', 'custom_early_reminder', 'repeat', 'repeat_end_date',
            'custom_repeat_interval', 'is_completed', 'completed_at', 'is_flagged',
            'priority', 'location', 'notification_preference',
            'tags', 'tag_ids', 'tag_names', 'subtasks', 'subtasks_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']
    
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        tag_names = validated_data.pop('tag_names', [])
        subtasks_data = validated_data.pop('subtasks_data', [])
        
        validated_data['user'] = self.context['request'].user
        
        reminder = Reminder.objects.create(**validated_data)
        
        if tags:
            reminder.tags.set(tags)
        
        if tag_names:
            user = validated_data.get('user')
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(
                    user=user,
                    name=tag_name
                )
                reminder.tags.add(tag)
        
        if subtasks_data:
            for subtask_data in subtasks_data:
                SubTask.objects.create(reminder=reminder, **subtask_data)
        
        return reminder
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        tag_names = validated_data.pop('tag_names', [])
        subtasks_data = validated_data.pop('subtasks_data', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update tags if provided
        if tags is not None:
            instance.tags.set(tags)
        
        if tag_names:
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(
                    user=instance.user,
                    name=tag_name
                )
                instance.tags.add(tag)
        
        if tags is None and tag_names:
            current_tags = list(instance.tags.all())
            tags = current_tags + tag_names

        # If both tags and new_tags were provided, we combine them
        elif tags is not None and tag_names:
            tags = list(tags) + tag_names

        # Update subtasks if provided
        if subtasks_data is not None:
            # Remove existing subtasks
            instance.subtasks.all().delete()
            
            # Create new subtasks
            for subtask_data in subtasks_data:
                SubTask.objects.create(reminder=instance, **subtask_data)
        
        return instance

class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'device_type', 'is_active']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # Check if token already exists for this user
        token = validated_data.get('token')
        device_type = validated_data.get('device_type')
        
        try:
            device_token = DeviceToken.objects.get(
                user=validated_data['user'],
                token=token
            )
            # Update existing token
            device_token.device_type = device_type
            device_token.is_active = True
            device_token.save()
            return device_token
        except DeviceToken.DoesNotExist:
            # Create new token
            return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'reminder', 'title', 'message', 'scheduled_time', 'sent', 'sent_at']
        read_only_fields = ['id', 'sent', 'sent_at']