"""Traino v2 — assessments/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    # Student
    path('<int:pk>/submit/',                    views.submit_assessment,      name='submit_assessment'),

    # Instructor
    path('submissions/',                        views.instructor_submissions, name='instructor_submissions'),
    path('submissions/<int:pk>/grade/',         views.grade_submission,       name='grade_submission'),
    path('assessments/<int:course_id>/create/',      views.create_assessment,      name='create_assessment'),
    path('<int:assessment_id>/questions/add/',  views.add_questions,          name='add_questions'),
]