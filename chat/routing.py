"""
Traino v2 — chat/routing.py
WebSocket URL routing for real-time chat.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # ws://localhost:8000/ws/chat/<room_id>/
    re_path(r'ws/chat/(?P<room_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]