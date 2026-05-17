"""
Traino v2 — Main URL Configuration
All app URLs are included here.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('admin/',          admin.site.urls),
    path('',                include('layouts.urls')),

    # Accounts — login/register/logout/profile etc.
    path('accounts/',       include('accounts.urls')),

    # Core feature apps
    path('courses/',        include('courses.urls')),
    path('instructor/',     include('instructor.urls')),
    path('student/',        include('student.urls')),
    path('assessments/',    include('assessments.urls')),
    path('notifications/',  include('notifications.urls')),

    # Namespaced apps — templates must use e.g. {% url 'chat:start_chat' id %}
    path('chat/',         include(('chat.urls',         'chat'),         namespace='chat')),
    path('shop/',         include(('shop.urls',         'shop'),         namespace='shop')),
    path('certificates/', include(('certificates.urls', 'certificates'), namespace='certificates')),
    path('chatbot/',      include(('chatbot.urls',      'chatbot'),      namespace='chatbot')),

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error pages
handler404 = 'layouts.views.error_404'
handler500 = 'layouts.views.error_500'

