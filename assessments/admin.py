from django.contrib import admin
from .models import Assessment, Question, Option, Submission, MCQAnswer

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display  = ['title', 'course', 'assess_type', 'mode', 'total_marks', 'due_date', 'created_at']
    list_filter   = ['assess_type', 'mode']
    search_fields = ['title', 'course__title']
    ordering      = ['-created_at']

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display  = ['student', 'assessment', 'marks', 'is_graded', 'submitted_at']
    list_filter   = ['is_graded']
    search_fields = ['student__email', 'assessment__title']
    ordering      = ['-submitted_at']
    readonly_fields = ['submitted_at']
