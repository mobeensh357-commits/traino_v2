


"""Traino v2 — chat/views.py"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import ChatRoom, ChatMessage
from courses.models import Course, Enrollment
from instructor.models import InstructorProfile

@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, pk=room_id)
    if request.user not in [room.student, room.instructor]:
        messages.error(request, 'Access denied.')
        return redirect('home')
    chat_messages = ChatMessage.objects.filter(room=room).order_by('timestamp')
    ChatMessage.objects.filter(room=room, is_read=False).exclude(sender=request.user).update(is_read=True)
    return render(request, 'chat/room.html', {
        'room': room,
        'chat_messages': chat_messages,
        'course': room.course,          # <-- add this line
    })
@login_required
def start_chat(request, course_id):
    course = get_object_or_404(Course, pk=course_id, status='approved')
    if request.user.is_student:
        enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        if not enrolled:
            messages.error(request, 'You must be enrolled to chat with the trainer.')
            return redirect('course_detail', pk=course_id)
        room, _ = ChatRoom.objects.get_or_create(
            student=request.user,
            instructor=course.instructor.user,
            course=course,
        )
        return redirect('chat:chat_room', room_id=room.pk)
    messages.error(request, 'Access denied.')
    return redirect('home')
