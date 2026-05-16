from django.db import models

# Create your models here.
"""
Traino v2 — chat/models.py
Real-time WebSocket chat between enrolled student and course instructor.
"""
from django.db import models
from django.conf import settings


class ChatRoom(models.Model):
    """One chat room per (student, instructor, course) combination."""
    student    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='student_rooms')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='instructor_rooms')
    course     = models.ForeignKey('courses.Course', on_delete=models.CASCADE,
                                   related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.course.title}: {self.student.username} ↔ {self.instructor.username}'

    class Meta:
        unique_together = ['student', 'instructor', 'course']
        ordering = ['-created_at']


class ChatMessage(models.Model):
    """A single message sent inside a ChatRoom."""
    room      = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='sent_messages')
    content   = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read   = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.sender.username}: {self.content[:40]}'

    class Meta:
        ordering = ['timestamp']