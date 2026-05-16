from django.db import models
from django.conf import settings
import uuid

class Certificate(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='certificates')
    cert_id = models.UUIDField(default=uuid.uuid4, unique=True, help_text='Unique ID for certificate verification.')
    pdf_file = models.FileField(upload_to='certificates/', null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # First save to get an ID if new
        super().save(*args, **kwargs)
        # Generate PDF if not already generated
        if not self.pdf_file:
            from .utils import generate_certificate_pdf
            generate_certificate_pdf(self)

    def __str__(self):
        return f'Certificate: {self.student.username} – {self.course.title}'

    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-issued_at']