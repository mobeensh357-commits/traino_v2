from django.contrib import admin
from .models import Assessment, Question, Option, Submission, MCQAnswer


def publish_assessments(modeladmin, request, queryset):
    queryset.update(is_published=True)
publish_assessments.short_description = "✅ Publish selected assessments (make visible to students)"


def unpublish_assessments(modeladmin, request, queryset):
    queryset.update(is_published=False)
unpublish_assessments.short_description = "🚫 Unpublish selected assessments (hide from students)"


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display   = ['title', 'course', 'assess_type', 'mode', 'total_marks', 'is_published', 'due_date', 'created_at']
    list_filter    = ['assess_type', 'mode', 'is_published']
    list_editable  = ['is_published']
    search_fields  = ['title', 'course__title']
    ordering       = ['-created_at']
    actions        = [publish_assessments, unpublish_assessments]
    fieldsets = (
        ('Assessment Info', {
            'fields': ('course', 'instructor', 'title', 'description', 'assess_type', 'mode')
        }),
        ('Settings', {
            'fields': ('total_marks', 'due_date', 'file', 'is_published')
        }),
    )


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display    = ['student', 'assessment', 'marks', 'is_graded', 'submitted_at']
    list_filter     = ['is_graded']
    search_fields   = ['student__email', 'assessment__title']
    ordering        = ['-submitted_at']
    readonly_fields = ['submitted_at']
