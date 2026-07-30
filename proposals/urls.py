from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import (
    ProposalViewSet, generate_proposal, estimate_proposal,
    export_proposal_pdf, send_proposal_for_review_view,
    send_proposal_to_client_view
)

router = DefaultRouter()
router.register(r'proposals', ProposalViewSet, basename='proposal')

urlpatterns = [
    path('generate/', generate_proposal, name='generate-proposal'),
    path('proposals/<int:pk>/estimate/', estimate_proposal, name='estimate-proposal'),
    path('proposals/<int:pk>/export-pdf/', export_proposal_pdf, name='export-proposal-pdf'),
    path('proposals/<int:pk>/send-for-review/', send_proposal_for_review_view, name='send-proposal-review'),
    path('proposals/<int:pk>/send-to-client/', send_proposal_to_client_view, name='send-proposal-client'),
] + router.urls