from django.urls import path
from . import consumers

#All the code in this file was written without assistance

#websocket route

websocket_urlpatterns = [
    path("ws/chat/<int:course_id>/", consumers.ChatConsumer.as_asgi()),
]