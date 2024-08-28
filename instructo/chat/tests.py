from django.test import TestCase
from .factories import MessageFactory
from courses.factories import CourseFactory, EnrollmentFactory
from users.factories import CustomUserFactory
from django.urls import reverse
from django.test import Client
from courses.models import Course
from .consumers import ChatConsumer
from channels.testing import WebsocketCommunicator, ChannelsLiveServerTestCase

# Create your tests here.
class GroupChatViewTest(TestCase):
    #method to create a teacher, students ,course, chat messages and enroll students - test attributes
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

class ChatConsumerTestCase(TestCase):
    #set up test attributes
    def setUp(self):
        #create an instance of the test client to simulate requests
        self.client = Client()

        #create a teacher
        self.teacher = CustomUserFactory(is_teacher=True, is_student=False)
        #create a student
        self.student = CustomUserFactory(is_teacher=False, is_student=True)
        #create a course
        self.course = CourseFactory(teacher=self.teacher)

        #log in student
        self.client.force_login(self.student)
    
    async def test_live_chat(self):
        #create a websocket communicator that will connect to the ChatConsumer for the given course
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.course.id}/")
        
        #attach the authenticated user to the websocket's connection scope
        communicator.scope["user"] = self.student
        #attach the url route params to the websocket's connection scope' - needed so that the ChatConsumer knows which course's chat is being accessed
        communicator.scope["url_route"] = {"kwargs": {"course_id": self.course.id}}
        
        #connect to the websocket
        connected, _ = await communicator.connect()

        #assert that the user is connected
        self.assertTrue(connected)

        #send a message in json format simulating the logic in out template script when the "Send" button is clicked
        await communicator.send_json_to({
            "message": "Hello Instructo User!",
            "sender": self.student.username
        })

        #receive the message from the websocket
        response = await communicator.receive_json_from()

        #assert that the message content is correct
        self.assertEqual(response["message"], "Hello Instructo User!")

        #assert that the sender is the student
        self.assertEqual(response["sender"], self.student.username)

        #disconnect the websockt communicator
        await communicator.disconnect()