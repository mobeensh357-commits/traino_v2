from django.urls import path
from . import views
urlpatterns = [
    path('review/<int:course_id>/', views.submit_review, name='submit_review'),
]
