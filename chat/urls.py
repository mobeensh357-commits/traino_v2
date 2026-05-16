from django.urls import path
from . import views

app_name = 'chat'   # <-- ADD THIS LINE

urlpatterns = [
    path('start/<int:course_id>/', views.start_chat, name='start_chat'),
    path('<int:room_id>/', views.chat_room, name='chat_room'),
]