from django.db import models

# Create your models here.
"""
Traino v2 — Instructor Models
Profile for trainers. Must be approved by Admin before publishing courses.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class InstructorProfile(models.Model):
    """
    Extended profile for users with is_teacher=True.
    Admin approves the profile before the trainer can create courses.
    """
    user        = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='instructor_profile',
    )
    full_name    = models.CharField(max_length=150, blank=True)
    designation  = models.CharField(max_length=100, blank=True, help_text='e.g. Certified Fitness Coach')
    bio          = models.TextField(max_length=1000, blank=True)
    experience   = models.TextField(max_length=1000, blank=True)
    education    = models.CharField(max_length=300, blank=True)
    phone        = models.CharField(max_length=20, blank=True)
    city         = models.CharField(max_length=100, blank=True)
    province     = models.CharField(max_length=100, blank=True)
    country      = models.CharField(max_length=100, blank=True, default='Pakistan')
    profile_pic  = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    document     = models.ImageField(
        upload_to='instructor_docs/',
        null=True, blank=True,
        help_text='Verification document. Admin reviews this before approval.',
    )
    is_approved  = models.BooleanField(
        default=False,
        help_text='Admin must approve before instructor can publish courses.',
    )
    rating       = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
    )
    total_students = models.PositiveIntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def get_display_name(self):
        """Return full_name or username fallback."""
        return self.full_name or self.user.username

    def __str__(self):
        return f'Instructor: {self.get_display_name()}'

    class Meta:
        verbose_name        = 'Instructor Profile'
        verbose_name_plural = 'Instructor Profiles'
        ordering            = ['-created_at']