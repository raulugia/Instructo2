from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message
from courses.models import Course
from users.models import CustomUser
import json
from asgiref.sync import sync_to_async

#All the code in this file was written without assistance

#websocket consumer for the live-chat
class ChatConsumer(AsyncWebsocketConsumer):
    #method that runs when the connection is established
    async def connect(self):
        #get the course id from the url
        self.course_id = self.scope["url_route"]["kwargs"]["course_id"]
        #create a unique group name
        self.course_group_name = f"chat_{self.course_id}"

        #add the connection to the course chat group
        await self.channel_layer.group_add(self.course_group_name, self.channel_name)
        #accept the connection
        await self.accept()

    #method that runs when the connection is closed
    async def disconnect(self, code):
        #remove the connection from the group chat group
        await self.channel_layer.group_discard(self.course_group_name, self.channel_name)
    
    #method that runs when a message is received from the websocket
    async def receive(self, text_data):
        #pase the message
        message_json = json.loads(text_data)

        #extract the message and sender
        message_content = message_json["message"]
        sender_username = message_json["sender"]

        #get sender and course asynchronously
        sender = await sync_to_async(CustomUser.objects.get)(username=sender_username)
        course = await sync_to_async(Course.objects.get)(id=self.course_id)

        #save the message to the database
        new_message = await sync_to_async(Message.objects.create)(
            sender = sender,
            content = message_content,
            course = course
        )

        #send the message to the course group chat asynchronously
        await self.channel_layer.group_send(
            self.course_group_name,
            {
                "type": "chat_message",
                "message": message_content,
                "sender": sender_username,
                "timestamp": new_message.timestamp.strftime("%Y-%m-%d %H:%M:")
            }
        )

    #method that sends messages to the websocket
    async def chat_message(self, event):
        #extract the message details
        message = event["message"]
        sender = event["sender"]
        timestamp = event["timestamp"]

        #send the message to the WebSocket
        await self.send(text_data=json.dumps({
            "message": message,
            "sender": sender,
            "timestamp": timestamp,
        }))

        