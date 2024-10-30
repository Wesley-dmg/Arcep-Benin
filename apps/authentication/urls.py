# -*- encoding: utf-8 -*-
from django.urls import path
from .views import *

app_name = "authentication"

urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path("logout/", logout_user, name="logout"),
    path('profile/', profile_view, name='profile'),  # Ajoutez cette ligne
]
