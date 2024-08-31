from django.db import models
from django.conf import settings
from courses.models import Course

#All the code in this file was written without assistance

#model representing the messages sent in a chat
#receiver can be null/blank as course group chats do not have a specific receiver
class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_messages", null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="messages")

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"

