from django.urls import path
from . import views

app_name = 'certificates'   # <-- ADD THIS LINE

urlpatterns = [
    path('download/<int:course_id>/', views.download_certificate, name='download_certificate'),
    path('verify/<uuid:cert_id>/', views.verify_certificate, name='verify_certificate'),
]