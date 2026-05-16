"""Traino v2 — feedback/views.py"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from .models import Review
from courses.models import Course, Enrollment

@login_required
def submit_review(request, course_id):
    if not request.user.is_student:
        messages.error(request, 'Only students can review courses.')
        return redirect('course_detail', pk=course_id)
    course = get_object_or_404(Course, pk=course_id, status='approved')
    enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    if not enrolled:
        messages.error(request, 'You must be enrolled to review this course.')
        return redirect('course_detail', pk=course_id)
    if request.method == 'POST':
        rating = request.POST.get('rating', '').strip()
        title  = request.POST.get('title', '').strip()
        body   = request.POST.get('body', '').strip()
        if not rating:
            messages.error(request, 'Please select a rating.')
            return redirect('course_detail', pk=course_id)
        try:
            rating = int(rating)
            if not 1 <= rating <= 5:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'Invalid rating.')
            return redirect('course_detail', pk=course_id)
        Review.objects.update_or_create(
            student=request.user, course=course,
            defaults={'rating': rating, 'title': title, 'body': body}
        )
        messages.success(request, 'Review submitted. Thank you!')
    return redirect('course_detail', pk=course_id)
