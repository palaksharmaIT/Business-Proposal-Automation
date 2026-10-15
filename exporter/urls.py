from django.urls import path

from proposals.views import download_proposal_pdf
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
        path('proposals/<int:pk>/download-pdf/', download_proposal_pdf, name='download-proposal-pdf'),
]