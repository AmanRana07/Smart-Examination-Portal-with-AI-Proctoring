# Generated by Django 3.0.5 on 2024-11-06 19:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0004_delete_course'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='email',
            field=models.EmailField(blank=True, max_length=100, null=True),
        ),
    ]
