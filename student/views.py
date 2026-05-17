# student views — to be implemented
"""
Traino v2 — student/views.py
Student dashboard, my courses, wishlist, progress.
"""
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.shortcuts import render, redirect, get_object_or_404

from .models import StudentProfile
from courses.models import Course, Enrollment, WishList
from assessments.models import Submission
from certificates.models import Certificate
from notifications.models import Notification

logger = logging.getLogger(__name__)


@login_required
def student_dashboard(request):
    """
    Student dashboard — enrolled courses, progress, recent submissions, certificates.
    """
    if not request.user.is_student:
        messages.error(request, 'Access denied. Student accounts only.')
        return redirect('home')

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('course', 'course__instructor').order_by('-enrolled_at')

    in_progress   = enrollments.filter(is_completed=False)
    completed     = enrollments.filter(is_completed=True)
    certificates  = Certificate.objects.filter(student=request.user).select_related('course')
    certificate_ids = Certificate.objects.filter(student=request.user).values_list('course_id', flat=True)
    recent_submissions = Submission.objects.filter(
        student=request.user
    ).select_related('assessment', 'assessment__course').order_by('-submitted_at')[:5]

    stats = {
        'enrolled':         enrollments.count(),
        'in_progress':      in_progress.count(),
        'completed':        completed.count(),
        'certificates':     certificates.count(),
    }

    return render(request, 'student/dashboard.html', {
        'profile':             profile,
        'stats':               stats,
        'in_progress':         in_progress[:6],
        'completed':           completed[:4],
        'certificates':        certificates[:3],
        'recent_submissions':  recent_submissions,
        'certificate_ids': certificate_ids,
    })

@login_required
def my_courses(request):
    """Shows all courses the student is enrolled in. Filter by status."""
    if not request.user.is_student:
        return redirect('home')

    status = request.GET.get('status', 'all')

    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('course', 'course__instructor').order_by('-enrolled_at')

    if status == 'in_progress':
        enrollments = enrollments.filter(is_completed=False)
    elif status == 'completed':
        enrollments = enrollments.filter(is_completed=True)

    # Get IDs of courses where certificate already exists
    from certificates.models import Certificate
    certificate_ids = Certificate.objects.filter(
        student=request.user
    ).values_list('course_id', flat=True)

    return render(request, 'student/my_courses.html', {
        'enrollments': enrollments,
        'status': status,
        'total': enrollments.count(),
        'certificate_ids': certificate_ids,
    })
@login_required
def wishlist(request):
    """Shows courses the student has wishlisted."""
    if not request.user.is_student:
        return redirect('home')

    wishes = WishList.objects.filter(
        student=request.user
    ).select_related('course', 'course__instructor').order_by('-added_at')

    return render(request, 'student/wishlist.html', {
        'wishes': wishes,
        'total':  wishes.count(),
    })


@login_required
def add_to_wishlist(request, course_id):
    """Toggle a course in/out of the student's wishlist."""
    if not request.user.is_student:
        return redirect('home')

    course = get_object_or_404(Course, pk=course_id, status='approved')
    obj, created = WishList.objects.get_or_create(student=request.user, course=course)

    if not created:
        obj.delete()
        messages.info(request, f'"{course.title}" removed from wishlist.')
    else:
        messages.success(request, f'"{course.title}" added to wishlist.')

    return redirect(request.META.get('HTTP_REFERER', 'wishlist'))


@login_required
def student_profile_edit(request):
    """Student profile edit page."""
    if not request.user.is_student:
        return redirect('home')

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        try:
            profile.full_name = request.POST.get('full_name', '').strip()
            profile.bio       = request.POST.get('bio', '').strip()
            profile.phone     = request.POST.get('phone', '').strip()
            profile.city      = request.POST.get('city', '').strip()
            profile.province  = request.POST.get('province', '').strip()
            profile.interests = request.POST.get('interests', '').strip()
            profile.education = request.POST.get('education', '').strip()

            if 'profile_pic' in request.FILES:
                profile.profile_pic = request.FILES['profile_pic']

            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('student_profile_edit')

        except DatabaseError as e:
            logger.error(f'Student profile update error: {e}')
            messages.error(request, 'Could not save profile. Please try again.')

    return render(request, 'student/profile_edit.html', {'profile': profile})


@login_required
def my_submissions_redirect(request):
    """Redirects to the actual my_submissions view in assessments app."""
    return redirect('my_submissions')