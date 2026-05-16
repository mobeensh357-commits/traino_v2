"""
Traino v2 — notifications/context_processors.py
Injects unread notification count into every template automatically.
"""
from .models import Notification


def unread_notifications_count(request):
    """
    Returns unread notification count for the navbar bell icon.
    Returns 0 for unauthenticated users.
    """
    if request.user.is_authenticated:
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:10]
        return {
            'unread_count': count,
            'recent_notifications': notifications,
        }
    return {'unread_count': 0, 'recent_notifications': []}