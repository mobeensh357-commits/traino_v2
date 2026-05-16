# instructor views — to be implemented
"""
Traino v2 — instructor/views.py
Instructor list, detail, dashboard, profile management.
"""
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.shortcuts import render, redirect, get_object_or_404

from .models import InstructorProfile
from courses.models import Course, Enrollment
from assessments.models import Submission
from notifications.models import Notification

logger = logging.getLogger(__name__)


def instructor_list(request):
    """
    Public page — lists all approved instructors.
    Supports search by name or designation.
    """
    query = request.GET.get('q', '').strip()
    instructors = InstructorProfile.objects.filter(
        is_approved=True
    ).select_related('user').order_by('-rating')

    if query:
        from django.db.models import Q
        instructors = instructors.filter(
            Q(full_name__icontains=query) |
            Q(designation__icontains=query) |
            Q(bio__icontains=query)
        )

    return render(request, 'instructor/list.html', {
        'instructors': instructors,
        'query': query,
        'total': instructors.count(),
    })


def instructor_detail(request, pk):
    """
    Public profile page for a single instructor.
    Shows their courses, rating, and bio.
    """
    instructor = get_object_or_404(InstructorProfile, pk=pk, is_approved=True)
    courses = Course.objects.filter(
        instructor=instructor, status='approved'
    ).order_by('-created_at')

    return render(request, 'instructor/detail.html', {
        'instructor': instructor,
        'courses': courses,
        'total_courses': courses.count(),
        'total_students': instructor.total_students,
    })


@login_required
def instructor_dashboard(request):
    """
    Instructor dashboard — shows stats, recent courses, and pending submissions.
    Redirects non-teachers away.
    """
    if not request.user.is_teacher:
        messages.error(request, 'Access denied. Instructor accounts only.')
        return redirect('home')

    try:
        profile = InstructorProfile.objects.get(user=request.user)
    except InstructorProfile.DoesNotExist:
        profile, _ = InstructorProfile.objects.get_or_create(user=request.user)

    courses = Course.objects.filter(
        instructor=profile
    ).order_by('-created_at')

    total_students = Enrollment.objects.filter(
        course__instructor=profile
    ).values('student').distinct().count()

    pending_submissions = Submission.objects.filter(
        assessment__instructor=profile,
        is_graded=False
    ).select_related('student', 'assessment')[:5]

    recent_courses = courses[:5]

    stats = {
        'total_courses':      courses.count(),
        'approved_courses':   courses.filter(status='approved').count(),
        'pending_courses':    courses.filter(status='pending').count(),
        'draft_courses':      courses.filter(status='draft').count(),
        'total_students':     total_students,
        'pending_submissions': pending_submissions.count(),
        'avg_rating':         profile.rating,
    }

    return render(request, 'instructor/dashboard.html', {
        'profile':             profile,
        'stats':               stats,
        'recent_courses':      recent_courses,
        'pending_submissions': pending_submissions,
    })


@login_required
def instructor_profile(request):
    """
    Instructor profile edit page.
    Handles both GET (display) and POST (update).
    """
    if not request.user.is_teacher:
        return redirect('home')

    profile, _ = InstructorProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        try:
            profile.full_name   = request.POST.get('full_name', '').strip()
            profile.designation = request.POST.get('designation', '').strip()
            profile.bio         = request.POST.get('bio', '').strip()
            profile.experience  = request.POST.get('experience', '').strip()
            profile.education   = request.POST.get('education', '').strip()
            profile.phone       = request.POST.get('phone', '').strip()
            profile.city        = request.POST.get('city', '').strip()
            profile.province    = request.POST.get('province', '').strip()

            if 'profile_pic' in request.FILES:
                profile.profile_pic = request.FILES['profile_pic']

            if 'document' in request.FILES:
                profile.document = request.FILES['document']
                # Reset approval when new document is uploaded
                profile.is_approved = False
                Notification.objects.create(
                    recipient=request.user,
                    title='Document Submitted for Verification',
                    message='Your verification document has been submitted. Admin will review it shortly.',
                    notif_type='info',
                )

            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('instructor_profile_edit')

        except DatabaseError as e:
            logger.error(f'Instructor profile update error: {e}')
            messages.error(request, 'Could not save profile. Please try again.')

    return render(request, 'instructor/profile_edit.html', {'profile': profile})


from chat.models import ChatRoom  # add at top


@login_required
def instructor_chat_list(request):
    """Show all chat rooms where the logged-in user is the instructor."""
    if not request.user.is_teacher:
        messages.error(request, 'Access denied.')
        return redirect('home')

    rooms = ChatRoom.objects.filter(instructor=request.user).order_by('-created_at')
    # Annotate last message for each room
    for room in rooms:
        room.last_message = room.messages.last()

    return render(request, 'instructor/chat_list.html', {'rooms': rooms})