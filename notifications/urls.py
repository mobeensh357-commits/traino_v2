"""Traino v2 — notifications/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path('',                      views.all_notifications, name='all_notifications'),
    path('mark-all-read/',        views.mark_all_read,     name='mark_all_read'),
    path('<int:pk>/click/',       views.notification_click, name='notification_click'),
]