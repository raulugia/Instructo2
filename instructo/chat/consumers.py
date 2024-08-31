from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message
from courses.models import Course
from users.models import CustomUser
import json
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        #get the course id from the url
        self.course_id = self.scope["url_route"]["kwargs"]["course_id"]
        #create a unique group name
        self.course_group_name = f"chat_{self.course_id}"

        #add the connection to the course chat group
        await self.channel_layer.group_add(self.course_group_name, self.channel_name)
        #accept the connection
        await self.accept()

    
    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.course_group_name, self.channel_name)
    
    async def receive(self, text_data):
        message_json = json.loads(text_data)
        message_content = message_json["message"]
        sender_username = message_json["sender"]

        #get sender and course with sync_to_async
        sender = await sync_to_async(CustomUser.objects.get)(username=sender_username)
        course = await sync_to_async(Course.objects.get)(id=self.course_id)

        #save the message to the database
        new_message = await sync_to_async(Message.objects.create)(
            sender = sender,
            content = message_content,
            course = course
        )

        #send the message to the course group chat
        await self.channel_layer.group_send(
            self.course_group_name,
            {
                "type": "chat_message",
                "message": message_content,
                "sender": sender_username,
                "timestamp": new_message.timestamp.strftime("%Y-%m-%d %H:%M:")
            }
        )

    async def chat_message(self, event):
        message = event["message"]
        sender = event["sender"]
        timestamp = event["timestamp"]

        #send the message to the WebSocket
        await self.send(text_data=json.dumps({
            "message": message,
            "sender": sender,
            "timestamp": timestamp,
        }))

        