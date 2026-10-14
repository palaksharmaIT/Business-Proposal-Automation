from django.urls import path
from . import views

urlpatterns = [
    # Public homepage
    path("", views.public_home, name="home"),

    # Authentication
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # Existing dashboard — keep unchanged
    path("dashboard/", views.dashboard_home, name="dashboard-home"),
]