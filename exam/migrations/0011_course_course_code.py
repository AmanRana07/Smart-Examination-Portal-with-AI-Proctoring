# Generated by Django 3.0.5 on 2024-11-14 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0010_course_creator'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='course_code',
            field=models.CharField(blank=True, max_length=10, unique=True),
        ),
    ]
