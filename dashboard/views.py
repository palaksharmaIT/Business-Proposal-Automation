from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError


# Public homepage — always show the new homepage UI
def public_home(request):
    return render(request, "dashboard/home.html")


# Existing proposal dashboard
@login_required(login_url="login")
def dashboard_home(request):
    return render(request, "dashboard/index.html")


# Login
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard-home")

    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard-home")

        error = "Invalid username or password."

    return render(request, "dashboard/login.html", {"error": error})


# Registration
def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard-home")

    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username or not email or not password or not confirm_password:
            error = "All fields are required."

        elif password != confirm_password:
            error = "Passwords do not match."

        elif User.objects.filter(username__iexact=username).exists():
            error = "Username already exists."

        elif User.objects.filter(email__iexact=email).exists():
            error = "Email is already registered."

        else:
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                login(request, user)
                return redirect("dashboard-home")

            except IntegrityError:
                error = "Unable to create account. Please try again."

    return render(request, "dashboard/register.html", {"error": error})


# Logout
def logout_view(request):
    logout(request)
    return redirect("login")
