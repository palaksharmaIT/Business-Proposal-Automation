from django.urls import path
from .views import dashboard_home , login_view, logout_view

urlpatterns = [
    path('', dashboard_home, name='dashboard-home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]