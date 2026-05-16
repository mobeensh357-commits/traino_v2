# accounts views — to be implemented
"""
Traino v2 — accounts/views.py
Handles: Register, Login, Logout, OTP Password Reset, Profile.
"""
import random
import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail, BadHeaderError
from django.db import DatabaseError
from django.shortcuts import render, redirect

from .forms import RegisterForm
from .models import User, OTP
from instructor.models import InstructorProfile
from student.models import StudentProfile
from notifications.models import Notification

logger = logging.getLogger(__name__)


def register(request):
    """
    Register a new Student or Instructor.
    Students are active immediately.
    Instructors are inactive until admin approves their profile.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        role = request.POST.get('role', '').strip()

        if role not in ['student', 'instructor']:
            messages.error(request, 'Please select a valid role.')
            return render(request, 'accounts/register.html', {'form': form})

        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.email    = form.cleaned_data['email'].lower()
                user.username = form.cleaned_data['username']

                if role == 'student':
                    user.is_student  = True
                    user.is_verified = True
                    user.save()
                    # Auto-create student profile
                    StudentProfile.objects.get_or_create(user=user)
                    # Welcome notification
                    Notification.objects.create(
                        recipient=user,
                        title='Welcome to Traino!',
                        message='Your student account is ready. Start exploring courses.',
                        notif_type='success',
                        link='/courses/',
                    )
                    login(request, user)
                    messages.success(request, f'Welcome, {user.username}! Start exploring courses.')
                    return redirect('student_dashboard')

                else:  # instructor
                    user.is_teacher  = True
                    user.is_verified = False   # Needs admin approval
                    user.save()
                    InstructorProfile.objects.get_or_create(user=user)
                    messages.success(
                        request,
                        'Instructor account created! Please complete your profile '
                        'and wait for admin approval before publishing courses.'
                    )
                    login(request, user)
                    return redirect('instructor_dashboard')

            except DatabaseError as e:
                logger.error(f'Register DB error: {e}')
                messages.error(request, 'Registration failed. Please try again.')
        else:
            messages.error(request, 'Please fix the errors below.')

    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    """Login using email and password."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Please enter your email and password.')
            return render(request, 'accounts/login.html')

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=email, password=password)
        if user is None:
            messages.error(request, 'Incorrect password. Please try again.')
            return render(request, 'accounts/login.html')

        login(request, user)
        messages.success(request, f'Welcome back, {user.username}!')

        if user.is_teacher:
            return redirect('instructor_dashboard')
        if user.is_student:
            return redirect('student_dashboard')
        return redirect('home')

    return render(request, 'accounts/login.html')


def user_logout(request):
    """Log out and redirect to home."""
    logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect('home')


def forgot_password(request):
    """Send 6-digit OTP to user's email for password reset."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'accounts/forgot_password.html')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal whether email exists
            messages.success(request, 'If this email is registered, an OTP has been sent.')
            return redirect('verify_otp')

        code = str(random.randint(100000, 999999))
        OTP.objects.filter(user=user).delete()   # Delete old OTPs
        OTP.objects.create(user=user, code=code)

        try:
            send_mail(
                subject='Traino — Your Password Reset OTP',
                message=f'Hi {user.username},\n\nYour OTP is: {code}\n\nValid for 10 minutes. Do not share it.\n\nTraino Team',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except (BadHeaderError, Exception) as e:
            logger.error(f'OTP email error: {e}')
            messages.error(request, 'Could not send OTP. Please try again.')
            return render(request, 'accounts/forgot_password.html')

        request.session['reset_email'] = email
        messages.success(request, 'OTP sent to your email address.')
        return redirect('verify_otp')

    return render(request, 'accounts/forgot_password.html')


def verify_otp(request):
    """Verify the OTP entered by the user."""
    if request.method == 'POST':
        entered = request.POST.get('otp', '').strip()
        email   = request.session.get('reset_email')

        if not email:
            messages.error(request, 'Session expired. Please start again.')
            return redirect('forgot_password')

        try:
            user = User.objects.get(email=email)
            otp  = OTP.objects.filter(user=user, code=entered, is_used=False).order_by('-created_at').first()

            if otp:
                otp.is_used = True
                otp.save()
                messages.success(request, 'OTP verified. Set your new password.')
                return redirect('reset_password')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')

        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('forgot_password')

    return render(request, 'accounts/verify_otp.html')


def reset_password(request):
    """Allow user to set a new password after OTP verification."""
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('forgot_password')

    if request.method == 'POST':
        pw1 = request.POST.get('password1', '').strip()
        pw2 = request.POST.get('password2', '').strip()

        if not pw1 or not pw2:
            messages.error(request, 'Please fill in both password fields.')
        elif pw1 != pw2:
            messages.error(request, 'Passwords do not match.')
        elif len(pw1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            try:
                user = User.objects.get(email=email)
                user.password = make_password(pw1)
                user.save(update_fields=['password'])
                OTP.objects.filter(user=user).delete()
                del request.session['reset_email']
                messages.success(request, 'Password reset successfully. Please sign in.')
                return redirect('login')
            except (User.DoesNotExist, DatabaseError) as e:
                logger.error(f'Reset password error: {e}')
                messages.error(request, 'Error resetting password. Please try again.')

    return render(request, 'accounts/reset_password.html')


@login_required
def profile(request):
    """View and update the current user's profile."""
    user = request.user

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name  = request.POST.get('last_name', '').strip()

        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']

        user.save(update_fields=['first_name', 'last_name', 'profile_picture'])

        if user.is_teacher:
            p = getattr(user, 'instructor_profile', None)
            if p:
                p.full_name   = f"{user.first_name} {user.last_name}".strip()
                p.bio         = request.POST.get('bio', '').strip()
                p.designation = request.POST.get('designation', '').strip()
                p.phone       = request.POST.get('phone', '').strip()
                p.city        = request.POST.get('city', '').strip()
                p.province    = request.POST.get('province', '').strip()
                p.experience  = request.POST.get('experience', '').strip()
                p.education   = request.POST.get('education', '').strip()
                if 'profile_pic' in request.FILES:
                    p.profile_pic = request.FILES['profile_pic']
                if 'document' in request.FILES:
                    p.document = request.FILES['document']
                p.save()

        elif user.is_student:
            p = getattr(user, 'student_profile', None)
            if p:
                p.full_name = f"{user.first_name} {user.last_name}".strip()
                p.bio       = request.POST.get('bio', '').strip()
                p.phone     = request.POST.get('phone', '').strip()
                p.city      = request.POST.get('city', '').strip()
                p.province  = request.POST.get('province', '').strip()
                p.interests = request.POST.get('interests', '').strip()
                p.education = request.POST.get('education', '').strip()
                if 'profile_pic' in request.FILES:
                    p.profile_pic = request.FILES['profile_pic']
                p.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    return render(request, 'accounts/profile.html', {'u': user})


@login_required
def change_password(request):
    """Change password for logged-in user."""
    if request.method == 'POST':
        current = request.POST.get('current_password', '')
        new1    = request.POST.get('new_password1', '')
        new2    = request.POST.get('new_password2', '')

        if not request.user.check_password(current):
            messages.error(request, 'Current password is incorrect.')
        elif new1 != new2:
            messages.error(request, 'New passwords do not match.')
        elif len(new1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            request.user.set_password(new1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')

    return render(request, 'accounts/change_password.html')