from django.contrib import admin

# Register your models here.
"""Traino v2 — student/admin.py"""
from django.contrib import admin
from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display  = ['get_display_name', 'user', 'city', 'education', 'joined_at']
    search_fields = ['full_name', 'user__email', 'city']
    list_filter   = ['education']
    ordering      = ['-joined_at']
    readonly_fields = ['joined_at']