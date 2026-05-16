"""Traino v2 — courses/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    # Public course list & detail
    path('',                      views.course_list,         name='course_list'),
    path('<int:pk>/',             views.course_detail,       name='course_detail'),

    # Enrollment
    path('<int:pk>/enroll/',      views.enroll,              name='enroll'),

    # Instructor course creation & management
    path('create/',               views.course_create,       name='course_create'),
    path('<int:pk>/manage/',      views.course_manage,        name='course_manage'),
    path('<int:pk>/submit/',      views.submit_for_approval,  name='submit_for_approval'),

    # Sections
    path('section/<int:course_id>/add/', views.add_section, name='add_section'),
    # Add this line wherever you like, for example after the 'download_material' route
    path('review/<int:course_id>/submit/', views.submit_review, name='submit_review'),
    # Materials
    path('material/<int:section_id>/add/', views.add_material, name='add_material'),
    path('material/<int:pk>/download/',   views.download_material, name='download_material'),

    path('material/<int:material_id>/complete/', views.toggle_material_completion, name='toggle_material_completion'),

]