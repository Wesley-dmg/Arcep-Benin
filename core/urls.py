# -*- encoding: utf-8 -*-
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),                         
    path("", include("apps.authentication.urls", namespace="authentication")), 
    path("", include("apps.home.urls", namespace="home")) 
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
