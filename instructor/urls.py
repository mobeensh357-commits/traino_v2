"""Traino v2 — instructor/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path('',                views.instructor_list,    name='instructor_list'),
    path('<int:pk>/',       views.instructor_detail,  name='instructor_detail'),
    path('dashboard/',      views.instructor_dashboard, name='instructor_dashboard'),
    path('profile/edit/',   views.instructor_profile, name='instructor_profile_edit'),
    path('chats/', views.instructor_chat_list, name='instructor_chat_list'),
]