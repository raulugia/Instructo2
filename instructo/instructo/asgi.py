"""
ASGI config for instructo project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

# import os
# import django

# from django.core.asgi import get_asgi_application

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "instructo.settings")

# django.setup()

# application = get_asgi_application()
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "instructo.settings")

django.setup()
import chat.routing
import users.routing
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns + 
            users.routing.websocket_urlpatterns
        )
    ),
})