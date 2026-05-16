from django.contrib import admin

# Register your models here.
"""Traino v2 — instructor/admin.py"""
from django.contrib import admin
from .models import InstructorProfile


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display  = ['get_display_name', 'user', 'designation', 'is_approved', 'rating', 'total_students', 'created_at']
    list_filter   = ['is_approved']
    search_fields = ['full_name', 'user__email', 'designation']
    list_editable = ['is_approved']
    ordering      = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'total_students', 'rating']

    fieldsets = [
        ('User',        {'fields': ('user',)}),
        ('Profile',     {'fields': ('full_name', 'designation', 'bio', 'profile_pic', 'document')}),
        ('Details',     {'fields': ('experience', 'education', 'phone', 'city', 'province', 'country')}),
        ('Status',      {'fields': ('is_approved', 'rating', 'total_students')}),
        ('Timestamps',  {'fields': ('created_at', 'updated_at')}),
    ]

    def save_model(self, request, obj, form, change):
        """Send notification to instructor when admin approves their profile."""
        was_approved = change and InstructorProfile.objects.filter(
            pk=obj.pk, is_approved=False
        ).exists()
        super().save_model(request, obj, form, change)
        if was_approved and obj.is_approved:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=obj.user,
                title='Profile Approved!',
                message='Congratulations! Your instructor profile has been approved. You can now create and publish courses.',
                notif_type='success',
                link='/instructor/dashboard/',
            )