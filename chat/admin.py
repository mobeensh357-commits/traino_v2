from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ChatRoom, ChatMessage
@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display  = ['course', 'student', 'instructor', 'created_at']
    search_fields = ['course__title', 'student__email']
    ordering      = ['-created_at']
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display  = ['sender', 'room', 'content', 'timestamp', 'is_read']
    list_filter   = ['is_read']
    search_fields = ['sender__email', 'content']
    ordering      = ['-timestamp']
