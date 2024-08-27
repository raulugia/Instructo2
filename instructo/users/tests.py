from django.test import TestCase
from .factories import CustomUserFactory

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
