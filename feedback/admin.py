from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Review
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ['student', 'course', 'rating', 'is_visible', 'created_at']
    list_filter   = ['rating', 'is_visible']
    search_fields = ['student__email', 'course__title']
    list_editable = ['is_visible']
    ordering      = ['-created_at']
