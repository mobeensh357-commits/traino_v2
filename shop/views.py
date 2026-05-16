# shop views — to be implemented
"""Traino v2 — shop/views.py — Dummy payment system"""
import uuid, logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from .models import Order
from courses.models import Course, Enrollment
from notifications.models import Notification

logger = logging.getLogger(__name__)

@login_required
def checkout(request, course_id):
    if not request.user.is_student:
        messages.error(request, 'Only students can purchase courses.')
        return redirect('course_detail', pk=course_id)
    course = get_object_or_404(Course, pk=course_id, status='approved')
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('course_detail', pk=course_id)
    if request.method == 'POST':
        card = request.POST.get('card_number', '').strip()
        if not card:
            messages.error(request, 'Please enter card details.')
            return render(request, 'shop/checkout.html', {'course': course})
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    student=request.user, course=course,
                    amount=course.price, status='completed',
                    transaction_id=str(uuid.uuid4())[:12].upper()
                )
                Enrollment.objects.get_or_create(student=request.user, course=course)
                Course.objects.filter(pk=course_id).update(total_enrolled=course.total_enrolled + 1)
                Notification.objects.create(
                    recipient=request.user,
                    title='Payment Successful!',
                    message=f'You are now enrolled in "{course.title}". Txn ID: {order.transaction_id}',
                    notif_type='success', link=f'/courses/{course_id}/',
                )
            messages.success(request, f'Payment successful! Enrolled in "{course.title}".')
            return redirect('course_detail', pk=course_id)
        except Exception as e:
            logger.error(f'Payment error: {e}')
            messages.error(request, 'Payment failed. Please try again.')
    return render(request, 'shop/checkout.html', {'course': course})