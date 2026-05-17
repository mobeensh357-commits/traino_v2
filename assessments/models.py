from django.db import models

# Create your models here.
"""
Traino v2 — Assessments Models
Assignments and MCQ Quizzes with student submissions and grading.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings


class Assessment(models.Model):
    """
    An assignment or quiz attached to a Course.
    Two modes: file upload (PDF/doc) or MCQ quiz.
    """
    TYPE_CHOICES = [('assignment', 'Assignment'), ('quiz', 'MCQ Quiz')]
    MODE_CHOICES = [('file', 'File Upload'), ('mcq', 'MCQ Quiz')]

    course      = models.ForeignKey('courses.Course',
                                    on_delete=models.CASCADE, related_name='assessments')
    instructor  = models.ForeignKey('instructor.InstructorProfile',
                                    on_delete=models.CASCADE, related_name='assessments')
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assess_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='assignment')
    mode        = models.CharField(max_length=10, choices=MODE_CHOICES, default='file')
    file        = models.FileField(upload_to='assessments/', null=True, blank=True,
                                   help_text='Question paper PDF (for file-upload mode).')
    total_marks = models.PositiveIntegerField(default=100, validators=[MinValueValidator(1)])
    due_date    = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(
        default=False,
        help_text='Admin must publish this assessment before students can see or submit it.'
    )
    created_at  = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'{self.title} — {self.course.title}'

    class Meta:
        verbose_name = 'Assessment'
        verbose_name_plural = 'Assessments'
        ordering = ['-created_at']


class Question(models.Model):
    """A single MCQ question inside an Assessment."""
    assessment    = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    marks         = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    order         = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.question_text[:60]

    class Meta:
        ordering = ['order']


class Option(models.Model):
    """One answer option for a Question. Only one per question should be correct."""
    question    = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=300)
    is_correct  = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.option_text} ({"✓" if self.is_correct else "✗"})'


class Submission(models.Model):
    """
    A student's submission for an Assessment.
    One submission per student per assessment (unique_together).
    Instructor grades it and provides feedback.
    """
    assessment   = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    student      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='submissions')
    file         = models.FileField(upload_to='submissions/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    marks        = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    feedback     = models.TextField(blank=True)
    is_graded    = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.student.username} → {self.assessment.title}'

    class Meta:
        unique_together = ['assessment', 'student']
        ordering = ['-submitted_at']


class MCQAnswer(models.Model):
    """Records the option a student selected for a given question in an MCQ submission."""
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='mcq_answers')
    question   = models.ForeignKey(Question,   on_delete=models.CASCADE, related_name='student_answers')
    selected   = models.ForeignKey(Option,     on_delete=models.CASCADE)

    def is_correct(self):
        return self.selected.is_correct

    def __str__(self):
        return f'{self.submission.student.username} → Q{self.question.id}'