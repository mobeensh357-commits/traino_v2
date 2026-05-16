from django.db import models

# Create your models here.
"""
Traino v2 — Courses Models
Udemy-style: Course → Sections → Materials + Enrollment tracking.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta


LEVEL_CHOICES = [
    ('beginner',     'Beginner'),
    ('intermediate', 'Intermediate'),
    ('advanced',     'Advanced'),
]

CATEGORY_CHOICES = [
    ('fitness',      'Health & Fitness'),
    ('yoga',         'Yoga & Meditation'),
    ('cooking',      'Cooking & Nutrition'),
    ('technology',   'Technology & IT'),
    ('language',     'Language Learning'),
    ('business',     'Business & Finance'),
    ('design',       'Design & Creativity'),
    ('personal',     'Personal Development'),
    ('driving',      'Driving'),
    ('other',        'Other'),
]

STATUS_CHOICES = [
    ('draft',    'Draft'),
    ('pending',  'Pending Admin Approval'),
    ('approved', 'Approved & Published'),
    ('rejected', 'Rejected'),
]


class Course(models.Model):
    """
    A training course created by an Instructor.
    Must be approved by Admin before students can enroll.
    Structured like Udemy: Course → Sections → Materials.
    """
    instructor = models.ForeignKey(
        'instructor.InstructorProfile',
        on_delete=models.CASCADE,
        related_name='courses',
    )
    title        = models.CharField(max_length=200)
    slug         = models.SlugField(max_length=250, unique=True, blank=True)
    category     = models.CharField(max_length=50,  choices=CATEGORY_CHOICES, default='other')
    level        = models.CharField(max_length=20,  choices=LEVEL_CHOICES,    default='beginner')
    language     = models.CharField(max_length=50,  default='English')
    thumbnail    = models.ImageField(upload_to='course_images/', null=True, blank=True)
    preview_video = models.FileField(upload_to='course_previews/', null=True, blank=True,
                                     help_text='Short preview video shown before enrollment.')
    summary      = models.TextField(blank=True, help_text='Short description shown in course cards.')
    description  = models.TextField(blank=True, help_text='Full course description page.')
    requirements = models.TextField(blank=True, help_text='What students need before enrolling.')
    objectives   = models.TextField(blank=True, help_text='What students will learn.')
    price        = models.DecimalField(max_digits=8, decimal_places=2, default=0.00,
                                       validators=[MinValueValidator(0)])
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True,
                                        help_text='Filled by admin when course is rejected.')
    avg_rating   = models.FloatField(default=0.0,
                                     validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_enrolled = models.PositiveIntegerField(default=0)
    is_featured  = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def is_free(self):
        """Returns True if the course has no price."""
        return self.price == 0

    def __str__(self):
        return self.title

    class Meta:
        verbose_name        = 'Course'
        verbose_name_plural = 'Courses'
        ordering            = ['-created_at']


class Section(models.Model):
    """
    A chapter/section inside a Course (like Udemy's curriculum sections).
    e.g. 'Week 1 — Introduction', 'Module 2 — Advanced Techniques'
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    title  = models.CharField(max_length=200)
    order  = models.PositiveIntegerField(default=0, help_text='Display order inside the course.')

    def __str__(self):
        return f'{self.course.title} → {self.title}'

    class Meta:
        verbose_name        = 'Section'
        verbose_name_plural = 'Sections'
        ordering            = ['order']


class Material(models.Model):
    """
    A single learning resource inside a Section.
    Can be a video, PDF, image, or other file.
    Admin must verify materials before students can download them.
    """
    MATERIAL_TYPES = [
        ('video', 'Video'),
        ('pdf',   'PDF Document'),
        ('image', 'Image'),
        ('other', 'Other'),
    ]

    section     = models.ForeignKey(Section,  on_delete=models.CASCADE, related_name='materials')
    title       = models.CharField(max_length=200)
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPES, default='pdf')
    file        = models.FileField(upload_to='course_files/')
    description = models.TextField(blank=True)
    order       = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(
        default=False,
        help_text='Admin must verify before students can access.',
    )
    is_preview  = models.BooleanField(
        default=False,
        help_text='If True, visible to non-enrolled users as a free preview.',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.section.course.title} / {self.section.title} / {self.title}'

    class Meta:
        verbose_name        = 'Material'
        verbose_name_plural = 'Materials'
        ordering            = ['order']


class Enrollment(models.Model):
    """
    Records a student's enrollment in a course.
    Expires after 180 days. Tracks progress percentage.
    One enrollment per student per course (unique_together).
    """
    student     = models.ForeignKey('accounts.User',  on_delete=models.CASCADE, related_name='enrollments')
    course      = models.ForeignKey(Course,           on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    progress    = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        help_text='Completion percentage 0-100.',
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """Auto-set expiry date 180 days from enrollment."""
        if not self.expiry_date:
            self.expiry_date = timezone.now() + timedelta(days=180)
        if self.progress >= 100 and not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """True if enrollment has not expired."""
        return timezone.now() < self.expiry_date if self.expiry_date else True

    def __str__(self):
        return f'{self.student.username} → {self.course.title}'

    class Meta:
        unique_together     = ['student', 'course']
        verbose_name        = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        ordering            = ['-enrolled_at']


class WishList(models.Model):
    """
    Lets students save courses they want to enroll in later.
    """
    student    = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='wishlist')
    course     = models.ForeignKey(Course,          on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student.username} wishlisted {self.course.title}'

    class Meta:
        unique_together     = ['student', 'course']
        verbose_name        = 'Wish List Item'
        verbose_name_plural = 'Wish List'


class StudentMaterialProgress(models.Model):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='completed_materials')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'material')

    def __str__(self):
        return f"{self.student.username} - {self.material.title}"

from django.utils import timezone

def update_course_progress(student, course):
    total_materials = Material.objects.filter(section__course=course).count()
    if total_materials == 0:
        progress = 0
    else:
        completed = StudentMaterialProgress.objects.filter(
            student=student,
            material__section__course=course
        ).count()
        progress = int((completed / total_materials) * 100)

    enrollment, _ = Enrollment.objects.get_or_create(student=student, course=course)
    enrollment.progress = progress
    if progress >= 100 and not enrollment.is_completed:
        enrollment.is_completed = True
        enrollment.completed_at = timezone.now()
        # Create certificate (already handled in your code)
        from certificates.models import Certificate
        Certificate.objects.get_or_create(student=student, course=course)

    enrollment.save(update_fields=['progress', 'is_completed', 'completed_at'])