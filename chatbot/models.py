from django.db import models

# Create your models here.
"""
Traino v2 — chatbot/models.py
Rule-based FAQ chatbot. Admin adds Q&A pairs via Django admin.
"""
from django.db import models


class FAQ(models.Model):
    """
    A keyword-matched FAQ entry for the chatbot.
    The chatbot searches keywords in the user's message and returns the matching answer.
    """
    question   = models.CharField(max_length=300, help_text='Question as it would appear in the chat.')
    keywords   = models.CharField(max_length=500,
                                  help_text='Comma-separated trigger keywords. e.g. enroll,signup,register')
    answer     = models.TextField(help_text='Response the chatbot will show.')
    is_active  = models.BooleanField(default=True)
    priority   = models.PositiveIntegerField(default=0, help_text='Higher = checked first.')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_keywords_list(self):
        """Return keywords as a Python list."""
        return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]

    def __str__(self):
        return self.question[:80]

    class Meta:
        ordering = ['-priority', 'question']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'