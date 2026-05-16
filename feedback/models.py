from django.db import models

# Create your models here.
"""
Traino v2 — feedback/models.py
Student reviews and star ratings for courses (like Udemy).
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class Review(models.Model):
    """
    A star rating + text review left by a student for a course.
    One review per student per course. Automatically updates the
    course's avg_rating when saved.
    """
    student    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='reviews')
    course     = models.ForeignKey('courses.Course', on_delete=models.CASCADE,
                                   related_name='reviews')
    rating     = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='1 to 5 stars.',
    )
    title      = models.CharField(max_length=150, blank=True)
    body       = models.TextField(blank=True)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Recalculate course avg_rating on every save."""
        super().save(*args, **kwargs)
        visible = Review.objects.filter(course=self.course, is_visible=True)
        if visible.exists():
            avg = visible.aggregate(models.Avg('rating'))['rating__avg']
            self.course.avg_rating = round(avg, 1)
            self.course.save(update_fields=['avg_rating'])

    def __str__(self):
        return f'{self.student.username} — {self.course.title} ({self.rating}★)'

    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-created_at']