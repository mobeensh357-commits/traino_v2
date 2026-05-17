"""Traino v2 — assessments/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    # Student
    path('<int:pk>/submit/',                   views.submit_assessment,   name='submit_assessment'),
    path('<int:pk>/remove/',                   views.remove_submission,   name='remove_submission'),
    path('my-submissions/',                    views.my_submissions,      name='my_submissions'),

    # Instructor
    path('submissions/',                       views.instructor_submissions, name='instructor_submissions'),
    path('submissions/<int:pk>/grade/',        views.grade_submission,       name='grade_submission'),
    path('<int:course_id>/create/',            views.create_assessment,      name='create_assessment'),
    path('<int:assessment_id>/questions/add/', views.add_questions,          name='add_questions'),
]