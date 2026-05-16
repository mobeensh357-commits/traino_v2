from django.db import models

# Create your models here.
"""
Traino v2 — notifications/models.py
In-app bell icon notifications for all user types.
"""
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    In-app notification shown in the navbar bell icon dropdown.
    Types: info, success, warning, error.
    """
    TYPE_CHOICES = [
        ('info',    'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error',   'Error'),
    ]
    recipient  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='notifications')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    notif_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='info')
    link       = models.CharField(max_length=300, blank=True, help_text='Optional URL to redirect on click.')
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'[{self.notif_type}] {self.recipient.username}: {self.title}'

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'