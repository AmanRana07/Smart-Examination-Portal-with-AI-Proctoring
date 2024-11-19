from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pic/Student/', null=True, blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20, null=False)
    email = models.EmailField(
        max_length=100, null=True, blank=True
    )  # Added email field
    @property
    def get_name(self):
        return self.user.first_name + " " + self.user.last_name

    @property
    def get_instance(self):
        return self

    def __str__(self):
        return self.user.first_name

class StudentImage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='student_images/')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
