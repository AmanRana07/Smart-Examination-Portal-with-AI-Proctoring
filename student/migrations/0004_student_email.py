# Generated by Django 3.0.5 on 2024-11-18 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0003_studentimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='email',
            field=models.EmailField(blank=True, max_length=100, null=True),
        ),
    ]
