# layouts views — to be implemented
"""
Traino v2 — layouts/views.py
Home page, About, Contact, Events, Guideline, Support, Error pages.
"""
import logging
from django.contrib import messages
from django.db import DatabaseError
from django.shortcuts import render, redirect, get_object_or_404

from courses.models import Course, Enrollment
from instructor.models import InstructorProfile
from .models import Event, ContactMessage

logger = logging.getLogger(__name__)


def home(request):
    """
    Home page — shows featured courses, top instructors, and platform stats.
    Supports search via GET param 'q'.
    """
    query = request.GET.get('q', '').strip()

    try:
        courses_qs = Course.objects.filter(
            status='approved'
        ).select_related('instructor').order_by('-created_at')

        if query:
            from django.db.models import Q
            courses_qs = courses_qs.filter(
                Q(title__icontains=query) |
                Q(summary__icontains=query) |
                Q(category__icontains=query) |
                Q(instructor__full_name__icontains=query)
            )
            featured = courses_qs[:12]
        else:
            featured = courses_qs[:8]

        instructors = InstructorProfile.objects.filter(
            is_approved=True
        ).order_by('-rating')[:4]

        stats = {
            'total_courses': Course.objects.filter(status='approved').count(),
            'total_instructors': InstructorProfile.objects.filter(is_approved=True).count(),
            'total_enrollments': Enrollment.objects.count(),
        }

    except DatabaseError as e:
        logger.error(f'Home page DB error: {e}')
        featured = []
        instructors = []
        stats = {'total_courses': 0, 'total_instructors': 0, 'total_enrollments': 0}

    return render(request, 'layouts/home.html', {
        'featured_courses': featured,
        'instructors': instructors,
        'stats': stats,
        'query': query,
    })


def about(request):
    """Render the About Traino page."""
    return render(request, 'layouts/about.html')


def contact(request):
    """
    Contact Us page. Saves submitted messages to the database.
    """
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        phone   = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        msg     = request.POST.get('message', '').strip()

        if not name or not email or not msg:
            messages.error(request, 'Please fill in your name, email, and message.')
            return render(request, 'layouts/contact.html')

        try:
            ContactMessage.objects.create(
                name=name, email=email, phone=phone,
                subject=subject, message=msg
            )
            messages.success(request, 'Thank you! We will reply within 1 hour.')
            return redirect('contact')
        except DatabaseError as e:
            logger.error(f'Contact form DB error: {e}')
            messages.error(request, 'Could not save your message. Please try again.')

    return render(request, 'layouts/contact.html')


def events(request):
    """Events listing page."""
    events_qs = Event.objects.filter(is_active=True).order_by('date')
    return render(request, 'layouts/events.html', {'events': events_qs})


def event_detail(request, pk):
    """Single event detail page."""
    event = get_object_or_404(Event, pk=pk, is_active=True)
    return render(request, 'layouts/event_detail.html', {'event': event})


def guideline(request):
    """How it works / step-by-step guide page."""
    return render(request, 'layouts/guideline.html')


def support(request):
    """Help center / FAQ page."""
    return render(request, 'layouts/support.html')


def error_404(request, exception):
    """Custom 404 page."""
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    """Custom 500 page."""
    return render(request, 'errors/500.html', status=500)