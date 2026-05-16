from django.db import models

# Create your models here.
"""
Traino v2 — Student Models
Extended profile for users with is_student=True.
"""
from django.db import models
from django.conf import settings


class StudentProfile(models.Model):
    """
    Extended profile for users who are trainees/students.
    Automatically created when a student completes their first profile setup.
    """
    EDUCATION_CHOICES = [
        ('matric',      'Matric / O-Levels'),
        ('inter',       'Intermediate / A-Levels'),
        ('bachelors',   "Bachelor's Degree"),
        ('masters',     "Master's Degree"),
        ('phd',         'PhD'),
        ('other',       'Other'),
    ]

    user          = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
    )
    full_name     = models.CharField(max_length=150, blank=True)
    bio           = models.TextField(max_length=1000, blank=True)
    phone         = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    education     = models.CharField(max_length=20, choices=EDUCATION_CHOICES, blank=True)
    interests     = models.CharField(max_length=500, blank=True, help_text='e.g. Fitness, Coding, Design')
    city          = models.CharField(max_length=100, blank=True)
    province      = models.CharField(max_length=100, blank=True)
    country       = models.CharField(max_length=100, blank=True, default='Pakistan')
    profile_pic   = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    joined_at     = models.DateTimeField(auto_now_add=True)

    def get_display_name(self):
        """Return full_name or username fallback."""
        return self.full_name or self.user.username

    def __str__(self):
        return f'Student: {self.get_display_name()}'

    class Meta:
        verbose_name        = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
        ordering            = ['-joined_at']