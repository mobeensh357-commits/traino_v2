import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from django.conf import settings
from django.core.files.base import ContentFile

def generate_certificate_pdf(certificate):
    """
    Generate PDF for a certificate and save it to the pdf_file field.
    Returns the saved Certificate instance.
    """
    student = certificate.student
    course = certificate.course
    cert_id = str(certificate.cert_id)

    buffer = io.BytesIO()
    width, height = landscape(A4)
    p = canvas.Canvas(buffer, pagesize=landscape(A4))

    # Border
    p.setStrokeColorRGB(0.96, 0.77, 0.09)  # gold
    p.setLineWidth(4)
    p.rect(20, 20, width - 40, height - 40)

    # Main title
    p.setFont("Helvetica-Bold", 36)
    p.setFillColorRGB(0.96, 0.77, 0.09)
    p.drawCentredString(width / 2, height - 80, "CERTIFICATE OF COMPLETION")

    # Body
    p.setFont("Helvetica", 18)
    p.setFillColorRGB(0, 0, 0)
    p.drawCentredString(width / 2, height - 140, "This is to certify that")

    student_name = student.get_full_name() or student.username
    p.setFont("Helvetica-Bold", 28)
    p.drawCentredString(width / 2, height - 200, student_name)

    p.setFont("Helvetica", 18)
    p.drawCentredString(width / 2, height - 260, "has successfully completed the course")

    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(width / 2, height - 320, course.title)

    p.setFont("Helvetica", 14)
    p.drawCentredString(width / 2, height - 380, f"Completed on: {certificate.issued_at.strftime('%B %d, %Y')}")

    # Certificate ID
    p.setFont("Helvetica", 10)
    p.drawCentredString(width / 2, height - 440, f"Certificate ID: {cert_id}")

    # Signature line
    p.line(width - 150, height - 460, width - 40, height - 460)
    p.setFont("Helvetica", 10)
    p.drawString(width - 140, height - 475, "Traino Platform")

    p.showPage()
    p.save()

    buffer.seek(0)
    filename = f"certificate_{cert_id}.pdf"
    certificate.pdf_file.save(filename, ContentFile(buffer.read()), save=False)
    certificate.save(update_fields=['pdf_file'])

    return certificate