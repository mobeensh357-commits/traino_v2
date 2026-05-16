"""Traino v2 – certificates/views.py"""
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from .models import Certificate


@login_required
def download_certificate(request, course_id):
    # Get or create certificate for this student & course
    cert, created = Certificate.objects.get_or_create(
        student=request.user,
        course_id=course_id
    )
    # Generate PDF if missing
    if not cert.pdf_file:
        from .utils import generate_certificate_pdf
        generate_certificate_pdf(cert)

    # Serve the file
    return FileResponse(
        cert.pdf_file.open('rb'),
        as_attachment=True,
        filename=f"certificate_{cert.cert_id}.pdf"
    )
def verify_certificate(request, cert_id):
    try:
        cert = Certificate.objects.select_related('student', 'course').get(cert_id=cert_id)
        valid = True
    except Certificate.DoesNotExist:
        cert = None
        valid = False
    return render(request, 'certificates/verify.html', {'cert': cert, 'valid': valid})