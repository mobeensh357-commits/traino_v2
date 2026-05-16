"""
Traino v2 — chat/consumers.py
WebSocket consumer: handles real-time messages between student and instructor.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Handles WebSocket connections for a ChatRoom.
    Each room has a unique group name: chat_<room_id>.
    Messages are broadcast to all connections in the same group.
    """

    async def connect(self):
        """Called when a WebSocket connection is opened."""
        self.room_id   = self.scope['url_route']['kwargs']['room_id']
        self.room_group = f'chat_{self.room_id}'

        # Add this connection to the room's channel group
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Called when the WebSocket connection is closed."""
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        """
        Called when a message arrives from the browser.
        Saves the message to the database and broadcasts it to the room group.
        """
        try:
            data    = json.loads(text_data)
            content = data.get('message', '').strip()
            if not content:
                return

            user = self.scope['user']
            if not user.is_authenticated:
                return

            # Save message to database
            message = await self.save_message(user, content)

            # Broadcast to all connections in this room
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type':      'chat_message',
                    'message':   content,
                    'sender':    user.username,
                    'sender_id': user.id,
                    'timestamp': message.timestamp.strftime('%H:%M'),
                }
            )
        except (json.JSONDecodeError, KeyError, Exception) as e:
            await self.send(text_data=json.dumps({'error': 'Invalid message format.'}))

    async def chat_message(self, event):
        """Called when a message is received from the channel group. Sends it to the browser."""
        await self.send(text_data=json.dumps({
            'message':   event['message'],
            'sender':    event['sender'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_message(self, user, content):
        """Save a ChatMessage to the database (runs in thread pool, not async)."""
        from .models import ChatRoom, ChatMessage
        room = ChatRoom.objects.get(id=self.room_id)
        return ChatMessage.objects.create(room=room, sender=user, content=content)