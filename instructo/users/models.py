#imports
from django.db import models
from django.contrib.auth.models import AbstractUser
from courses.models import Resource

#All the code in this file was written without assistance

#create a custom user model where email is unique
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    date_of_birth = models.DateField()
    city = models.CharField(max_length=60)
    country = models.CharField(max_length=60)
    profile_picture = models.OneToOneField(Resource, null=True, blank=True, on_delete=models.SET_NULL, related_name="user_profile")
    is_student = models.BooleanField(default=True)
    is_teacher = models.BooleanField(default=False)

    #email will be used for authentication
    USERNAME_FIELD = "email"
    #required fields
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "date_of_birth", "city", "country"]

    def __str__(self):
        return self.username
