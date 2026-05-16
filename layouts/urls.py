"""Traino v2 — layouts/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path('',              views.home,         name='home'),
    path('about/',        views.about,        name='about'),
    path('contact/',      views.contact,      name='contact'),
    path('events/',       views.events,       name='events'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('guideline/',    views.guideline,    name='guideline'),
    path('support/',      views.support,      name='support'),
]