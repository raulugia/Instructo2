from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = f"{self.scope['user'].username}_notifications"

        #join the notifications group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        #leave notifications group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
    
    async def send_notification(self, event):
        #send the notification to the websocket
        await self.send(text_data = json.dumps({"message": event["message"]}))