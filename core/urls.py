# -*- encoding: utf-8 -*-
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),                         
    path("", include("apps.authentication.urls", namespace="authentication")), 
    path("", include("apps.home.urls", namespace="home")) 
]
