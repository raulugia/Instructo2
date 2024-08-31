from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        #create a unique group name that will be called when the connection is established
        self.group_name = f"{self.scope['user'].username}_notifications"

        #join the user to the notifications group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        #accept the connection
        await self.accept()

    #async method called when the connection is closed
    async def disconnect(self, close_code):
        #remove the user form the notifications group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
    
    #async method to send a notifications
    async def send_notification(self, event):
        #send the notification as JSON to the websocket
        await self.send(text_data = json.dumps({"message": event["message"]}))