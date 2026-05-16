# chatbot/urls.py
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('ask-chatbot/', views.ask_chatbot, name='ask-chatbot'),
]