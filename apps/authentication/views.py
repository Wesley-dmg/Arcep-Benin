# -*- encoding: utf-8 -*-
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import LoginForm, SignUpForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.urls import reverse

def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                msg = 'Identifiants invalides'
        else:
            msg = 'Erreur de validation du formulaire'
    context={
        "form": form, 
        "msg": msg
        }
    return render(request, "accounts/login.html", context)


def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            msg = 'Utilisateur créé - veuillez vous connecter <a href="/login">Se Connecter</a>.'
            success = True

            return redirect("/login/")

        else:
            msg = 'Le formulaire n\'est pas valide'
    else:
        form = SignUpForm()
    context= {
                "form": form, 
                "msg": msg, 
                "success": success
                }
    return render(request, "accounts/register.html",context)


def logout_user(request):
    logout(request)
    return redirect(reverse('authentication:login'))

@login_required
def profile_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email

        if password:
            user.set_password(password)
            update_session_auth_hash(request, user)  # Pour ne pas déconnecter l'utilisateur après changement du mot de passe

        user.save()

        messages.success(request, 'Votre profil a été mis à jour avec succès.')
        return redirect('authentication:profile')

    return render(request, 'home/profile.html')