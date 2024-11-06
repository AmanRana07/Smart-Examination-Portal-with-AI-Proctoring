from django import forms
from django.contrib.auth.models import User
from . import models


class TeacherUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "password",
            "email",
        ]  # Added 'email'
        widgets = {"password": forms.PasswordInput()}


class TeacherForm(forms.ModelForm):
    class Meta:
        model = models.Teacher
        fields = ["address", "mobile", "profile_pic", "email"]  # Added 'email'
