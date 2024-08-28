from django.test import TestCase
from .factories import MessageFactory
from courses.factories import CourseFactory, EnrollmentFactory
from users.factories import CustomUserFactory
from django.urls import reverse

# Create your tests here.
class GroupChatViewTest(TestCase):
    #method to create a teacher, students ,course chat messages and enroll students - test attributes
    def setUp(self):
        #create a teacher
        self.teacher = CustomUserFactory(is_teacher=True, is_student=False)
        #create student
        self.student = CustomUserFactory(is_teacher=False, is_student=True)
        
        #create a course
        self.course = CourseFactory(teacher=self.teacher)
        #enroll student
        EnrollmentFactory(course=self.course, student=self.student)

        #create chat messages
        self.message1 = MessageFactory(sender=self.student, course=self.course, content="Hello")
        self.message2 = MessageFactory(sender=self.teacher, course=self.course, content="Welcome to the course")
    
    #test method to ensure the course chat messages in the database are returned correctly so users can see the chat history
    def test_group_chat(self):
        #log in as the student
        self.client.force_login(self.student)

        #access the chat view
        response = self.client.get(reverse("group_chat_view", args=[self.course.id]))

        #assert that the messages content is in the response
        self.assertContains(response, self.message1.content)
        self.assertContains(response, self.message2.content)