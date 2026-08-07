from django.urls import path
from . import views

urlpatterns = [
    path(
        "delivery/approve/<uuid:token>/",
        views.approve_proposal,
        name="proposal-approve",
    ),

    path(
        "delivery/reject/<uuid:token>/",
        views.reject_proposal,
        name="proposal-reject",
    ),
]