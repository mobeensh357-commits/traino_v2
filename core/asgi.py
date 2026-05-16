"""
Traino v2 — ASGI Configuration
Handles both HTTP requests and WebSocket connections (real-time chat).
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = ProtocolTypeRouter({
    # Standard HTTP requests → Django
    'http': get_asgi_application(),
    # WebSocket connections → Django Channels (real-time chat)
    'websocket': AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})