from django.urls import path
from . import views

app_name = 'shop'   # <-- ADD THIS LINE

urlpatterns = [
    path('checkout/<int:course_id>/', views.checkout, name='checkout'),
]