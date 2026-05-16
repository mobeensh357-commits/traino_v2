# notifications views — to be implemented
"""Traino v2 — notifications/views.py"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404, render
from .models import Notification


@login_required
def all_notifications(request):
    """Show all notifications for the current user."""
    notifs = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    # Mark all as read when page is opened
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/all.html', {'notifications': notifs})


@login_required
def mark_all_read(request):
    """Mark all unread notifications as read (AJAX or redirect)."""
    Notification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def notification_click(request, pk):
    """
    Mark a single notification as read and redirect to its link.
    Called when user clicks a notification in the dropdown.
    """
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])

    if notif.link:
        return redirect(notif.link)
    return redirect('all_notifications')