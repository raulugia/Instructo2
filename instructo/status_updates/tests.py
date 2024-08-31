from django.test import TestCase
from django.urls import reverse
from users.factories import CustomUserFactory
from courses.factories import CourseFactory
from .models import StatusUpdate
from courses.factories import ResourceFactory

#All the code in this file was written without assistance

class CreateStatusUpdateViewTest(TestCase):

    #method to create a teacher, student and course needed for the tests - test attributes
    def setUp(self):
        #create a teacher
        self.teacher = CustomUserFactory(is_teacher=True, is_student=False)
        #create a student
        self.student = CustomUserFactory(is_teacher=False, is_student=True)
        #create a course
        self.course = CourseFactory(teacher=self.teacher)
        #create a resource
        self.file = ResourceFactory(file="https://example.com/path/to/file.pdf", resource_format="pdf", resource_type="status_update")
    
    #tets method to ensure teachers can create a status update linked to a course
    def test_teacher_creates_status_update_with_course(self):
        #log in as the teacher
        self.client.force_login(self.teacher)

        #create post data
        post_data = {
            "content": "This is a status update linked to a course.",
            "course": self.course.id
        }

        #send a POST request to create the status update
        response = self.client.post(reverse("status_updates:create_status_update_view"), data=post_data)

        #assert that the status update was created successfully
        self.assertTrue(StatusUpdate.objects.filter(user=self.teacher, content=post_data["content"], course=self.course).exists())
        
        #assert that redirection happens as expected
        self.assertRedirects(response, reverse("users:home_view"))
    
    #test method to ensure teachers can create status updates with files
    def test_teacher_creates_status_update_with_file(self):
        #log in as the teacher
        self.client.force_login(self.teacher)

        #create post data
        post_data = {
            "content": "This is a status update linked to a course.",
            "course": self.course.id
        }

        file_data = {"resource_file": self.file}

         #send a POST request to create the status update
        response = self.client.post(reverse("status_updates:create_status_update_view"), data=post_data, files=file_data)

        #fetch the status update
        status_update = StatusUpdate.objects.get(user=self.teacher, content=post_data["content"], course=self.course)

        #assert that the status update was created successfully
        self.assertIsNotNone(status_update)
        
        #assert that redirection happens as expected
        self.assertRedirects(response, reverse("users:home_view"))
