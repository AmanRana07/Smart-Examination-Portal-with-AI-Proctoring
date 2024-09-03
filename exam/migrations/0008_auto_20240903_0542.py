# Generated by Django 3.0.5 on 2024-09-03 05:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('exam', '0007_course_duration_minutes'),
    ]

    operations = [
        migrations.AddField(
            model_name='examsession',
            name='cancellation_flag',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='examsession',
            name='reload_detected',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='exam.ExamSession')),
            ],
        ),
    ]
