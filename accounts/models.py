from django.db import models

# Create your models here.
"""
Traino v2 — Accounts Models
Custom User model + OTP for password reset.
"""
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class User(AbstractUser):
    """
    Custom User model using email as the unique login identifier.
    Roles: is_student (Trainee) | is_teacher (Trainer).
    Trainers must be verified by admin before they can publish courses.
    """
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        max_length=150,
        unique=False,
        validators=[username_validator],
        help_text='Display name. Does not need to be unique.',
    )
    email = models.EmailField(
        unique=True,
        help_text='Used for login. Must be unique.',
    )
    is_student = models.BooleanField(default=False)
    is_teacher  = models.BooleanField(default=False)
    is_verified = models.BooleanField(
        default=False,
        help_text='Trainers must be verified by admin before publishing courses.',
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True, blank=True,
    )

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    def validate_unique(self, exclude=None):
        """Skip unique-check on username since duplicates are allowed."""
        exclude = exclude or set()
        exclude.add('username')
        super().validate_unique(exclude=exclude)

    def get_role(self):
        """Return human-readable role string."""
        if self.is_teacher:
            return 'Trainer'
        if self.is_student:
            return 'Trainee'
        return 'User'

    def __str__(self):
        return f'{self.username} ({self.email})'

    class Meta:
        verbose_name        = 'User'
        verbose_name_plural = 'Users'
        ordering            = ['-date_joined']


class OTP(models.Model):
    """
    Stores a 6-digit One-Time Password for password reset.
    One OTP per user — old OTPs are deleted when a new one is issued.
    """
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code       = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    def __str__(self):
        return f'OTP for {self.user.email} — {self.code}'

    class Meta:
        verbose_name        = 'OTP'
        verbose_name_plural = 'OTPs'
        ordering            = ['-created_at']