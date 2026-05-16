from django.contrib import admin

# Register your models here.
"""Traino v2 — accounts/admin.py"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['email', 'username', 'is_student', 'is_teacher', 'is_verified', 'is_active', 'date_joined']
    list_filter   = ['is_student', 'is_teacher', 'is_verified', 'is_active']
    search_fields = ['email', 'username']
    ordering      = ['-date_joined']
    fieldsets     = BaseUserAdmin.fieldsets + (
        ('Traino Roles', {'fields': ('is_student', 'is_teacher', 'is_verified', 'profile_picture')}),
    )
    list_editable = ['is_verified', 'is_active']


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display  = ['user', 'code', 'is_used', 'created_at']
    list_filter   = ['is_used']
    search_fields = ['user__email']