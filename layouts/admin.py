from django.contrib import admin

# Register your models here.
"""Traino v2 — layouts/admin.py"""
from django.contrib import admin
from .models import Event, ContactMessage


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display  = ['title', 'date', 'location', 'is_active', 'created_at']
    list_filter   = ['is_active', 'date']
    search_fields = ['title', 'location']
    list_editable = ['is_active']
    ordering      = ['date']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display  = ['name', 'email', 'subject', 'is_read', 'submitted_at']
    list_filter   = ['is_read']
    search_fields = ['name', 'email', 'subject']
    list_editable = ['is_read']
    ordering      = ['-submitted_at']
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'submitted_at']