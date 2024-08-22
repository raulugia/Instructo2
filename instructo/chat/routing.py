from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/chat/<int:course_id>/", consumers.ChatConsumer.as_asgi()),
]