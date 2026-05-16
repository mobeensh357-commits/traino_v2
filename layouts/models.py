from django.db import models

# Create your models here.
"""
Traino v2 — layouts/models.py
Home page content: Events and Contact messages.
"""
from django.db import models


class Event(models.Model):
    """A training event or webinar displayed on the Events page."""
    title       = models.CharField(max_length=200)
    image       = models.ImageField(upload_to='events/', null=True, blank=True)
    description = models.TextField()
    location    = models.CharField(max_length=200)
    date        = models.DateField()
    start_time  = models.TimeField()
    end_time    = models.TimeField()
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} — {self.date}'

    class Meta:
        ordering = ['date']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'


class ContactMessage(models.Model):
    """Stores messages submitted through the Contact Us page."""
    name       = models.CharField(max_length=100)
    email      = models.EmailField()
    phone      = models.CharField(max_length=20, blank=True)
    subject    = models.CharField(max_length=150, blank=True)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} — {self.subject}'

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'