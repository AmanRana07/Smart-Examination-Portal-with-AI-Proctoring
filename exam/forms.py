from django import forms
from django.contrib.auth.models import User
from . import models
from .models import Course


class ContactusForm(forms.Form):
    Name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "w-full p-4 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            }
        ),
    )

    Email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "w-full p-4 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            }
        )
    )

    Message = forms.CharField(
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "cols": 30,
                "class": "w-full p-4 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500",
            }
        ),
    )


class TeacherSalaryForm(forms.Form):
    salary = forms.IntegerField()


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["course_name", "question_number", "total_marks", "duration_minutes"]
        widgets = {
            "course_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter course name"}
            ),
            "question_number": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Example: 10", "min": 1}
            ),
            "total_marks": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Example: 100", "min": 1}
            ),
            "duration_minutes": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: 60",
                    "min": 1,  # Ensure that only positive values can be entered
                }
            ),
        }


class QuestionForm(forms.ModelForm):

    # this will show dropdown __str__ method course model is shown on html so override it
    # to_field_name this will fetch corresponding value  user_id present in course model and return it
    courseID = forms.ModelChoiceField(queryset=Course.objects.none())

    class Meta:
        model = models.Question
        fields = [
            "courseID",
            "question",
            "marks",
            "option1",
            "option2",
            "option3",
            "option4",
            "answer",
        ]
        widgets = {"question": forms.Textarea(attrs={"rows": 3, "cols": 50})}
