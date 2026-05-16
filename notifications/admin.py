"""Traino v2 — notifications/admin.py"""
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['recipient', 'title', 'notif_type', 'is_read', 'created_at']
    list_filter   = ['notif_type', 'is_read']
    search_fields = ['recipient__email', 'title', 'message']
    list_editable = ['is_read']
    ordering      = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient')