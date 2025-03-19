# Generated by Django 5.1.7 on 2025-03-17 12:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0002_subtask_completed_at_subtask_created_at_subtask_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='subtask',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='reminders.subtask'),
        ),
    ]
