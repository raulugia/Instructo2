from django.test import TestCase
from users.factories import CustomUserFactory
from courses.factories import CourseFactory, EnrollmentFactory
from rest_framework.test import APIClient
from django.urls import reverse
