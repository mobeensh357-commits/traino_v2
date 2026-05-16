"""Traino v2 — student/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/',           views.student_dashboard,    name='student_dashboard'),
    path('my-courses/',          views.my_courses,           name='my_courses'),
    path('wishlist/',            views.wishlist,              name='wishlist'),
    path('wishlist/add/<int:course_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('profile/edit/',        views.student_profile_edit, name='student_profile_edit'),
]