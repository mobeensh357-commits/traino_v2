from django.db import models

# Create your models here.
"""
Traino v2 — shop/models.py
Dummy payment system — simulates Udemy-style course purchase flow.
"""
from django.db import models
from django.conf import settings


class Order(models.Model):
    """
    Represents a completed course purchase.
    Status flow: pending → completed (dummy — no real payment gateway).
    """
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('completed', 'Completed'),
        ('failed',    'Failed'),
        ('refunded',  'Refunded'),
    ]
    student       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                      related_name='orders')
    course        = models.ForeignKey('courses.Course', on_delete=models.CASCADE,
                                      related_name='orders')
    amount        = models.DecimalField(max_digits=8, decimal_places=2)
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True,
                                      help_text='Dummy transaction reference number.')
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Order #{self.id} — {self.student.username} — {self.course.title} ({self.status})'

    class Meta:
        ordering = ['-created_at']