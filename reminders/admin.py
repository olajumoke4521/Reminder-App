from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import (
    Reminder, SubTask, Tag,
    DeviceToken, Notification
)


class SubTaskInline(admin.TabularInline):
    model = SubTask
    extra = 1
    fields = ('title', 'is_completed', 'priority', 'date', 'time', 'is_flagged')
    show_change_link = True


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'date', 'time', 'priority_badge', 'is_completed', 
        'is_flagged', 'user', 'tag_list', 'subtasks_count'
    )
    list_filter = ('is_completed', 'is_flagged', 'priority', 'repeat', 'date')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    filter_horizontal = ('tags',)
    inlines = [SubTaskInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'user')
        }),
        ('Date & Time', {
            'fields': ('date', 'time', 'is_all_day')
        }),
        ('Notification', {
            'fields': ('early_reminder', 'custom_early_reminder')
        }),
        ('Recurring', {
            'fields': ('repeat', 'repeat_end_date', 'custom_repeat_interval')
        }),
        ('Status', {
            'fields': ('is_completed', 'completed_at', 'is_flagged', 'priority')
        }),
        ('Additional Information', {
            'fields': ('tags',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def priority_badge(self, obj):
        colors = {
            'none': '#808080',  
            'low': '#3498db',  
            'medium': '#f39c12', 
            'high': '#e74c3c',  
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 7px; '
            'border-radius: 5px;">{}</span>',
            colors.get(obj.priority, '#808080'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def tag_list(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    tag_list.short_description = 'Tags'
    
    def subtasks_count(self, obj):
        count = obj.subtasks.count()
        completed = obj.subtasks.filter(is_completed=True).count()
        if count == 0:
            return '0'
        return f"{completed}/{count}"
    subtasks_count.short_description = 'Subtasks'
    
    actions = ['mark_as_completed', 'mark_as_uncompleted', 'toggle_flag']
    
    def mark_as_completed(self, request, queryset):
        for reminder in queryset:
            reminder.mark_as_completed()
        self.message_user(request, f"{queryset.count()} reminders marked as completed.")
    mark_as_completed.short_description = "Mark selected reminders as completed"
    
    def mark_as_uncompleted(self, request, queryset):
        queryset.update(is_completed=False, completed_at=None)
        self.message_user(request, f"{queryset.count()} reminders marked as uncompleted.")
    mark_as_uncompleted.short_description = "Mark selected reminders as uncompleted"
    
    def toggle_flag(self, request, queryset):
        for reminder in queryset:
            reminder.is_flagged = not reminder.is_flagged
            reminder.save()
        self.message_user(request, f"Flagged status toggled for {queryset.count()} reminders.")
    toggle_flag.short_description = "Toggle flagged status for selected reminders"


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'reminder_link', 'date', 'time', 'priority_badge', 
        'is_completed', 'is_flagged', 'user', 'tag_list'
    )
    list_filter = ('is_completed', 'is_flagged', 'priority', 'date')
    search_fields = ('title', 'description', 'reminder__title')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    filter_horizontal = ('tags',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'reminder')
        }),
        ('Date & Time', {
            'fields': ('date', 'time', 'is_all_day')
        }),
        ('Status', {
            'fields': ('is_completed', 'completed_at', 'is_flagged', 'priority')
        }),
        ('Organization', {
            'fields': ('tags', 'order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def priority_badge(self, obj):
        colors = {
            'none': '#808080',  
            'low': '#3498db',   
            'medium': '#f39c12', 
            'high': '#e74c3c',  
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 7px; '
            'border-radius: 5px;">{}</span>',
            colors.get(obj.priority, '#808080'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def reminder_link(self, obj):
        url = reverse('admin:reminders_reminder_change', args=[obj.reminder.id])
        return format_html('<a href="{}">{}</a>', url, obj.reminder.title)
    reminder_link.short_description = 'Reminder'
    
    def user(self, obj):
        return obj.reminder.user
    user.short_description = 'User'
    
    def tag_list(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    tag_list.short_description = 'Tags'
    
    actions = ['mark_as_completed', 'mark_as_uncompleted', 'toggle_flag']
    
    def mark_as_completed(self, request, queryset):
        for subtask in queryset:
            subtask.mark_as_completed()
        self.message_user(request, f"{queryset.count()} subtasks marked as completed.")
    mark_as_completed.short_description = "Mark selected subtasks as completed"
    
    def mark_as_uncompleted(self, request, queryset):
        queryset.update(is_completed=False, completed_at=None)
        self.message_user(request, f"{queryset.count()} subtasks marked as uncompleted.")
    mark_as_uncompleted.short_description = "Mark selected subtasks as uncompleted"
    
    def toggle_flag(self, request, queryset):
        for subtask in queryset:
            subtask.is_flagged = not subtask.is_flagged
            subtask.save()
        self.message_user(request, f"Flagged status toggled for {queryset.count()} subtasks.")
    toggle_flag.short_description = "Toggle flagged status for selected subtasks"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'reminders_count', 'subtasks_count', 'total_count')
    list_filter = ('user',)
    search_fields = ('name',)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _reminders_count=Count('reminders', distinct=True),
            _subtasks_count=Count('subtasks', distinct=True)
        )
        return queryset
    
    def reminders_count(self, obj):
        return obj._reminders_count
    reminders_count.short_description = 'Reminders'
    reminders_count.admin_order_field = '_reminders_count'
    
    def subtasks_count(self, obj):
        return obj._subtasks_count
    subtasks_count.short_description = 'Subtasks'
    subtasks_count.admin_order_field = '_subtasks_count'
    
    def total_count(self, obj):
        return obj._reminders_count + obj._subtasks_count
    total_count.short_description = 'Total Usage'

    actions = ['merge_tags']
    
    def merge_tags(self, request, queryset):
        if queryset.count() < 2:
            self.message_user(request, "Select at least two tags to merge.", level='error')
            return
            
        # Check if all tags belong to the same user
        users = set(queryset.values_list('user', flat=True))
        if len(users) > 1:
            self.message_user(request, "Cannot merge tags belonging to different users.", level='error')
            return
            
        # Use the first tag as the primary tag
        primary_tag = queryset.first()
        other_tags = queryset.exclude(id=primary_tag.id)
        
        # Move all reminders and subtasks to the primary tag
        for tag in other_tags:
            for reminder in tag.reminders.all():
                reminder.tags.add(primary_tag)
            
            for subtask in tag.subtasks.all():
                subtask.tags.add(primary_tag)
                
        # Delete the other tags
        count = other_tags.count()
        names = ", ".join([tag.name for tag in other_tags])
        other_tags.delete()
        
        self.message_user(
            request, 
            f"Successfully merged {count} tags ({names}) into '{primary_tag.name}'."
        )
    merge_tags.short_description = "Merge selected tags (first tag is kept)"
    
    def get_readonly_fields(self, request, obj=None):
        if obj: 
            return self.readonly_fields + ('reminders_count', 'subtasks_count', 'total_count')
        return self.readonly_fields


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'is_active', 'last_used')
    list_filter = ('device_type', 'is_active', 'user')
    readonly_fields = ('last_used',)
    search_fields = ('user__username', 'token')
    
    actions = ['activate_tokens', 'deactivate_tokens']
    
    def activate_tokens(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} device tokens activated.")
    activate_tokens.short_description = "Activate selected device tokens"
    
    def deactivate_tokens(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} device tokens deactivated.")
    deactivate_tokens.short_description = "Deactivate selected device tokens"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'reminder_link', 'scheduled_time', 'sent', 'sent_at')
    list_filter = ('sent', 'scheduled_time', 'user')
    search_fields = ('title', 'message', 'user__username', 'reminder__title')
    readonly_fields = ('sent', 'sent_at')
    
    def reminder_link(self, obj):
        url = reverse('admin:reminders_reminder_change', args=[obj.reminder.id])
        return format_html('<a href="{}">{}</a>', url, obj.reminder.title)
    reminder_link.short_description = 'Reminder'