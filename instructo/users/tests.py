from django.test import TestCase
from .factories import CustomUserFactory
from django.urls import reverse
from .models import CustomUser

#All the code in this file was written without assistance

class CustomUserModelTest(TestCase):

    #test method to verify users can be created
    def test_user_creation(self):
        #use the factory to create a new user
        user = CustomUserFactory()

        #assert that the username was created successfully
        self.assertEqual(user.username, f"user_{user.id}")
        
        #assert that the password was set correctly
        self.assertTrue(user.check_password("password"))
    
    #test method to verify that the profile picture was set correctly
    def test_profile_picture(self):
        #use the factory to create a new user
        user = CustomUserFactory()

        #assert that the profile picture was created successfully
        self.assertIsNotNone(user.profile_picture)
        
        #assert that the resource type is correct
        self.assertEqual(user.profile_picture.resource_type, "user_profile_picture")
        
        #assert that the resource format is correct
        self.assertEqual(user.profile_picture.resource_format, "image")
    
    #test method to verify users can sign in
    def test_user_sign_in(self):
        #use the factory to create a new user
        user = CustomUserFactory()

        #simulate a POST request to the sign in url with the sign in details
        response = self.client.post(reverse("users:signIn_view"), {
            "email": user.email,
            "password": "password"
        })

        #assert that the response redirects the user to the home page
        self.assertRedirects(response, reverse("users:home_view"))

        #assert that the user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    #test method to verify users can logout
    def test_user_log_out(self):
        #use the factory to create a new user
        user = CustomUserFactory()

        #simulate a GET request to the logout url
        response = self.client.get(reverse("users:logout_view"))

        #assert that the user is not authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)

class RegisterViewTest(TestCase):

    #test method to verify registration is successful
    def test_teacher_registration(self):
        #fake post data
        post_data = {
            "username": "mike.smith",
            "email": "mike@instructo.com",
            "password1": "09Po87iu.",
            "password2": "09Po87iu.",
            "first_name": "Mike",
            "last_name": "Smith",
            "date_of_birth": "1993-08-07",
            "city": "Madrid",
            "country": "Spain",
            "account_type": "teacher"
        }

        #send a POST request to the register view with the fake data
        response = self.client.post(reverse("users:register_view"), post_data)

        #assert that the user was redirected to the sign in page
        self.assertRedirects(response, reverse("users:signIn_view"))

        #check that the user is in the database
        #get the user
        user = CustomUser.objects.get(email="mike@instructo.com")
        #assert that it exists
        self.assertIsNotNone(user)
        #assert the password is correct
        self.assertTrue(user.check_password("09Po87iu."))
        #assert user is a teacher
        self.assertTrue(user.is_teacher)
        #assert user is not a student
        self.assertFalse(user.is_student)
    
    #test method to verify user cannot register if passwords do not match
    def test_registration_mismatched_passwords(self):
        #fake post data
        post_data = {
            "username": "mike.smith",
            "email": "mike@instructo.com",
            "password1": "09Po87iu.",
            "password2": "09pO87iu.",
            "first_name": "Mike",
            "last_name": "Smith",
            "date_of_birth": "1993-08-07",
            "city": "Madrid",
            "country": "Spain",
            "account_type": "teacher"
        }

        #send a POST request to the register view with the fake data
        response = self.client.post(reverse("users:register_view"), post_data)

        #check if the form is rendered again with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match")

        #ensure the user does not exist in the database
        self.assertFalse(CustomUser.objects.filter(email="mike@instructo.com").exists())