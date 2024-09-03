from django import forms
from django.contrib.auth.models import User
from . import models
from .models import Course


class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))

class TeacherSalaryForm(forms.Form):
    salary=forms.IntegerField()

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_name', 'question_number', 'total_marks', 'duration_minutes']
        widgets = {
            'course_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter course name'
            }),
            'question_number': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Example: 10',
                'min': 1
            }),
            'total_marks': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Example: 100',
                'min': 1
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Example: 60',
                'min': 1  # Ensure that only positive values can be entered
            }),
        }

class QuestionForm(forms.ModelForm):
    
    #this will show dropdown __str__ method course model is shown on html so override it
    #to_field_name this will fetch corresponding value  user_id present in course model and return it
    courseID=forms.ModelChoiceField(queryset=models.Course.objects.all(),empty_label="Course Name", to_field_name="id")
    class Meta:
        model=models.Question
        fields=['marks','question','option1','option2','option3','option4','answer']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3, 'cols': 50})
        }
