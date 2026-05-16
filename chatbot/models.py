"""
Traino v2 — chatbot/models.py
Rule-based FAQ chatbot. Admin manages Q&A pairs via Django admin.
The chatbot matches user messages using keywords and returns answers.
"""

from django.conf import settings
from django.db import models
class FAQ(models.Model):
    """
    A keyword-matched FAQ entry for the Traino chatbot.
    The chatbot checks the user message against all active FAQs
    and returns the best match based on keyword overlap.

    Fields:
        question   : The question as shown in the chat (display only)
        keywords   : Comma-separated trigger words the chatbot looks for
        answer     : The response shown to the user
        category   : Groups FAQs for easier admin management
        is_active  : Inactive FAQs are skipped
        priority   : Higher priority FAQs are checked first
    """
    CATEGORY_CHOICES = [
        ('enrollment',  'Enrollment & Courses'),
        ('account',     'Account & Profile'),
        ('payment',     'Payment & Pricing'),
        ('trainer',     'Trainers & Approval'),
        ('technical',   'Technical Support'),
        ('certificate', 'Certificates'),
        ('general',     'General'),
    ]

    question   = models.CharField(max_length=300)
    keywords   = models.CharField(
        max_length=500,
        help_text='Comma-separated trigger words. e.g. enroll,join,register,course'
    )
    answer     = models.TextField()
    category   = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general'
    )
    is_active  = models.BooleanField(default=True)
    priority   = models.PositiveIntegerField(
        default=0,
        help_text='Higher number = checked first when keywords match.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_keywords_list(self):
        """Return cleaned list of keyword strings."""
        return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]

    def match_score(self, message):
        """
        Return how many keywords from this FAQ appear in the message.
        Used to pick the best-matching FAQ.
        """
        msg_lower = message.lower()
        return sum(1 for kw in self.get_keywords_list() if kw in msg_lower)

    def __str__(self):
        return f'[{self.get_category_display()}] {self.question[:60]}'

    class Meta:
        ordering            = ['-priority', 'question']
        verbose_name        = 'FAQ'
        verbose_name_plural = 'FAQs'



class ChatHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True, db_index=True)
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Chat histories'

    def __str__(self):
        return f"{self.user or self.session_id}: {self.message[:50]}"