from django.contrib import admin

# Register your models here.
# chatbot/admin.py
from django.contrib import admin
from .models import FAQ

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'priority', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'keywords', 'answer']
    ordering = ['-priority', 'question']