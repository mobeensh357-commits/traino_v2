"""
Traino v2 — Main URL Configuration
All app URLs are included here.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as accounts_views

urlpatterns = [

    path('admin/',          admin.site.urls),
    path('',                include('layouts.urls')),
    path('signin/', accounts_views.user_login, name='signin'),
    path('signup/', accounts_views.register, name='signup'),
    path('accounts/',       include('accounts.urls')),
    path('courses/',        include('courses.urls')),
    path('instructor/',     include('instructor.urls')),
    path('student/',        include('student.urls')),
    path('assessments/',    include('assessments.urls')),
    path('chat/',           include('chat.urls')),

    # Namespaced apps — templates must use e.g. {% url 'chat:chat_room' id %}
    path('chat/',         include(('chat.urls',         'chat'),         namespace='chat')),
    path('shop/',         include(('shop.urls',         'shop'),         namespace='shop')),
    path('certificates/', include(('certificates.urls', 'certificates'), namespace='certificates')),
    path('notifications/',  include('notifications.urls')),
    path('chatbot/',        include('chatbot.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error pages
handler404 = 'layouts.views.error_404'
handler500 = 'layouts.views.error_500'

