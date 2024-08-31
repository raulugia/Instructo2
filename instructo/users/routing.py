from django.urls import path
from . import consumers

#All the code in this file was written without assistance

#url pattern for the websocket

websocket_urlpatterns = [
    path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
]