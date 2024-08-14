from django.db import models

from student.models import Student
class Course(models.Model):
   course_name = models.CharField(max_length=50)
   question_number = models.PositiveIntegerField()
   total_marks = models.PositiveIntegerField()
   def __str__(self):
        return self.course_name

class Question(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    marks=models.PositiveIntegerField()
    question=models.CharField(max_length=600)
    option1=models.CharField(max_length=200)
    option2=models.CharField(max_length=200)
    option3=models.CharField(max_length=200)
    option4=models.CharField(max_length=200)
    cat=(('Option1','Option1'),('Option2','Option2'),('Option3','Option3'),('Option4','Option4'))
    answer=models.CharField(max_length=200,choices=cat)

class Result(models.Model):
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    exam = models.ForeignKey(Course,on_delete=models.CASCADE)
    marks = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now=True)

class ExamSession(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    suspicious_activity_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Exam session for {self.student} in {self.course.course_name}"

class ProctoringEvent(models.Model):
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    def __str__(self):
        return f"Proctoring Event: {self.event_type} at {self.timestamp} for session {self.session}"

class SuspiciousActivity(models.Model):
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    def __str__(self):
        return f"Suspicious Activity: {self.activity_type} at {self.timestamp} for session {self.session}"
